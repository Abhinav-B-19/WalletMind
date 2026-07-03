"""Validate AI assistant answers for grounding against retrieved context."""

from __future__ import annotations

import re
from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal

from backend.app.services.assistant.context_builder import AssistantContext
from walletmind.exceptions import AssistantValidationError


class AnswerValidator:
    """Guardrails ensuring assistant answers remain grounded and non-hallucinatory."""

    _MONTH_NAME_TO_NUMBER = {
        "january": 1,
        "february": 2,
        "march": 3,
        "april": 4,
        "may": 5,
        "june": 6,
        "july": 7,
        "august": 8,
        "september": 9,
        "october": 10,
        "november": 11,
        "december": 12,
    }
    _AMOUNT_QUANTIZER = Decimal("0.01")

    def validate(self, *, answer: str, context: AssistantContext) -> None:
        """Validate non-empty, context-grounded assistant answer text."""

        cleaned_answer = answer.strip()
        if not cleaned_answer:
            raise AssistantValidationError("Assistant response is empty.")

        if self._contains_unavailable_phrase(cleaned_answer):
            return

        known_merchants = {
            (tx.get("merchant") or "").strip().lower()
            for tx in context.transactions
            if (tx.get("merchant") or "").strip()
        }
        known_transaction_ids = {
            str(tx.get("transaction_id", "")).strip().lower()
            for tx in context.transactions
            if str(tx.get("transaction_id", "")).strip()
        }
        known_dates = {
            str(tx.get("date", "")).strip()
            for tx in context.transactions
            if str(tx.get("date", "")).strip()
        }

        self._validate_merchant_claims(
            answer=cleaned_answer,
            known_merchants=known_merchants,
        )
        self._validate_transaction_claims(
            answer=cleaned_answer,
            known_transaction_ids=known_transaction_ids,
        )
        self._validate_date_claims(
            answer=cleaned_answer,
            known_dates=known_dates,
        )
        self._validate_numeric_claims(
            answer=cleaned_answer,
            context=context,
        )

    def _validate_merchant_claims(
        self,
        *,
        answer: str,
        known_merchants: set[str],
    ) -> None:
        if not known_merchants:
            return

        candidate_patterns = [
            r"(?:at|from|merchant)\s+([^\n\.,;:!?]+)",
            r"for\s+([^\n\.,;:!?]+)\s+(?:was|is|are|total|spent)",
        ]
        mentioned_candidates: list[str] = []
        lowered = answer.lower()
        for pattern in candidate_patterns:
            for match in re.finditer(pattern, lowered, flags=re.IGNORECASE):
                candidate = match.group(1).strip(" '")
                if candidate:
                    mentioned_candidates.append(candidate)

        for candidate in mentioned_candidates:
            if candidate in {"least", "most", "total", "average"}:
                continue
            if not any(
                known in candidate or candidate in known for known in known_merchants
            ):
                raise AssistantValidationError(
                    "Assistant response references merchants not in retrieved data."
                )

    def _validate_transaction_claims(
        self,
        *,
        answer: str,
        known_transaction_ids: set[str],
    ) -> None:
        transaction_refs = {
            token.lower()
            for token in re.findall(
                r"\b(?:tx-[a-z0-9\-]+|[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})\b",
                answer,
                flags=re.IGNORECASE,
            )
        }
        unsupported_refs = [
            ref for ref in transaction_refs if ref not in known_transaction_ids
        ]
        if unsupported_refs:
            raise AssistantValidationError(
                "Assistant response references transactions not in retrieved data."
            )

    def _validate_date_claims(
        self,
        *,
        answer: str,
        known_dates: set[str],
    ) -> None:
        if not known_dates:
            return

        known_months = {
            int(date_text.split("-")[1])
            for date_text in known_dates
            if re.match(r"^\d{4}-\d{2}-\d{2}$", date_text)
        }

        mentioned_iso_dates = set(re.findall(r"\b\d{4}-\d{2}-\d{2}\b", answer))
        invalid_iso_dates = [
            date_text
            for date_text in mentioned_iso_dates
            if date_text not in known_dates
        ]
        if invalid_iso_dates:
            raise AssistantValidationError(
                "Assistant response references dates not in retrieved data."
            )

        month_mentions = {
            self._MONTH_NAME_TO_NUMBER[month_name.lower()]
            for month_name in re.findall(
                r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\b",
                answer,
            )
        }
        unsupported_months = [
            month_value
            for month_value in month_mentions
            if month_value not in known_months
        ]
        if unsupported_months:
            raise AssistantValidationError(
                "Assistant response references months not in retrieved data."
            )

    def _validate_numeric_claims(
        self,
        *,
        answer: str,
        context: AssistantContext,
    ) -> None:
        monetary_claims, percentage_claims = self._extract_numeric_claims(answer)
        if not monetary_claims and not percentage_claims:
            return

        derivable_amounts, derivable_percentages = self._build_derivable_numeric_space(
            context
        )

        unsupported_amounts = [
            value
            for value in monetary_claims
            if self._round_amount(value) not in derivable_amounts
        ]
        if unsupported_amounts:
            raise AssistantValidationError(
                "Assistant response contains amounts not derivable from retrieved data."
            )

        unsupported_percentages = [
            value
            for value in percentage_claims
            if self._round_amount(value) not in derivable_percentages
        ]
        if unsupported_percentages:
            raise AssistantValidationError(
                "Assistant response contains percentages not derivable "
                "from retrieved data."
            )

    def _build_derivable_numeric_space(
        self,
        context: AssistantContext,
    ) -> tuple[set[Decimal], set[Decimal]]:
        amounts: list[Decimal] = []
        debit_amounts: list[Decimal] = []
        credit_amounts: list[Decimal] = []
        merchant_totals: defaultdict[tuple[str, str], Decimal] = defaultdict(
            lambda: Decimal("0")
        )
        category_totals: defaultdict[tuple[str, str], Decimal] = defaultdict(
            lambda: Decimal("0")
        )
        month_totals: defaultdict[tuple[str, str], Decimal] = defaultdict(
            lambda: Decimal("0")
        )

        for tx in context.transactions:
            amount = self._round_amount(Decimal(str(tx.get("amount", 0))))
            abs_amount = self._round_amount(abs(amount))
            amounts.append(abs_amount)

            tx_type = str(tx.get("transaction_type", "")).lower()
            if tx_type == "debit":
                debit_amounts.append(abs_amount)
            elif tx_type == "credit":
                credit_amounts.append(abs_amount)

            merchant_key = (str(tx.get("merchant", "")).strip().lower(), tx_type)
            category_key = (str(tx.get("category", "")).strip().lower(), tx_type)
            month_key = (str(tx.get("date", "")).strip()[:7], tx_type)

            merchant_totals[merchant_key] += abs_amount
            category_totals[category_key] += abs_amount
            month_totals[month_key] += abs_amount

        derivable_amounts: set[Decimal] = {
            self._round_amount(Decimal(str(context.summary.get("total_amount", 0)))),
            self._round_amount(Decimal(str(context.summary.get("average_amount", 0)))),
            self._round_amount(Decimal(str(context.summary.get("max_amount", 0)))),
            self._round_amount(Decimal(str(context.summary.get("min_amount", 0)))),
            Decimal("0.00"),
        }

        derivable_amounts.update({self._round_amount(value) for value in amounts})
        derivable_amounts.update({self._round_amount(value) for value in debit_amounts})
        derivable_amounts.update(
            {self._round_amount(value) for value in credit_amounts}
        )

        total_abs = self._round_amount(sum(amounts, Decimal("0")))
        total_debits = self._round_amount(sum(debit_amounts, Decimal("0")))
        total_credits = self._round_amount(sum(credit_amounts, Decimal("0")))

        aggregate_values = {
            total_abs,
            total_debits,
            total_credits,
            self._round_amount(total_credits - total_debits),
            self._safe_average(amounts),
            self._safe_average(debit_amounts),
            self._safe_average(credit_amounts),
        }
        aggregate_values.update(
            {self._round_amount(value) for value in merchant_totals.values()}
        )
        aggregate_values.update(
            {self._round_amount(value) for value in category_totals.values()}
        )
        aggregate_values.update(
            {self._round_amount(value) for value in month_totals.values()}
        )
        derivable_amounts.update(aggregate_values)

        aggregate_list = list(aggregate_values)
        for left in aggregate_list:
            for right in aggregate_list:
                derivable_amounts.add(self._round_amount(abs(left - right)))

        derivable_percentages: set[Decimal] = {Decimal("0.00"), Decimal("100.00")}
        denominator_candidates = {total_abs, total_debits, total_credits}
        numerator_candidates = set(aggregate_values)

        for numerator in numerator_candidates:
            for denominator in denominator_candidates:
                if denominator == Decimal("0.00"):
                    continue
                percentage = self._round_amount((numerator / denominator) * 100)
                derivable_percentages.add(percentage)

        return derivable_amounts, derivable_percentages

    def _extract_numeric_claims(
        self, answer: str
    ) -> tuple[list[Decimal], list[Decimal]]:
        percentage_claims: list[Decimal] = []
        percentage_spans: list[tuple[int, int]] = []
        for match in re.finditer(r"(-?\d+(?:\.\d+)?)\s*%", answer):
            percentage_claims.append(self._round_amount(Decimal(match.group(1))))
            percentage_spans.append(match.span())

        monetary_claims: list[Decimal] = []
        monetary_pattern = re.compile(
            r"(?<![A-Za-z0-9/\-])(?P<prefix>\$|USD\s*)?(?P<number>-?(?:\d{1,3}(?:,\d{3})+|\d+(?:\.\d{1,2})?))(?![A-Za-z0-9/\-])",
            flags=re.IGNORECASE,
        )
        for match in monetary_pattern.finditer(answer):
            if "%" in match.group(0):
                continue
            match_span = match.span()
            if any(
                match_span[0] >= pct_span[0] and match_span[1] <= pct_span[1]
                for pct_span in percentage_spans
            ):
                continue
            raw_number = match.group("number").replace(",", "")
            prefix = (match.group("prefix") or "").strip().lower()

            if (
                not prefix
                and "." not in raw_number
                and raw_number.lstrip("-").isdigit()
            ):
                integer_value = int(raw_number)
                if 1900 <= integer_value <= 2100:
                    continue

            monetary_claims.append(self._round_amount(Decimal(raw_number)))

        return monetary_claims, percentage_claims

    def _round_amount(self, value: Decimal) -> Decimal:
        return value.quantize(self._AMOUNT_QUANTIZER, rounding=ROUND_HALF_UP)

    def _safe_average(self, values: list[Decimal]) -> Decimal:
        if not values:
            return Decimal("0.00")
        return self._round_amount(sum(values, Decimal("0")) / Decimal(len(values)))

    @staticmethod
    def _contains_unavailable_phrase(answer: str) -> bool:
        lowered = answer.lower()
        phrases = [
            "cannot determine",
            "not available",
            "insufficient data",
            "unable to determine",
        ]
        return any(phrase in lowered for phrase in phrases)
