"""Deterministic retrieval service for assistant query grounding."""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from walletmind.schemas.transaction import TransactionDTO
from walletmind.services.transaction_service import TransactionService


@dataclass(frozen=True)
class RetrievalResult:
    """Subset of transactions matched for an assistant question."""

    statement_uuid: UUID
    question: str
    filters_applied: dict[str, str]
    transactions: list[TransactionDTO]


class RetrievalService:
    """Retrieve relevant transactions for a natural-language question."""

    _CATEGORY_KEYWORDS = {
        "food": "Food & Dining",
        "fuel": "Fuel",
        "rent": "Rent",
        "income": "Income",
        "salary": "Income",
        "subscription": "Entertainment",
    }

    _PAYMENT_CHANNEL_KEYWORDS = {
        "upi": "UPI",
        "card": "Card",
        "atm": "ATM",
        "cash": "Cash",
        "bank transfer": "Bank Transfer",
    }

    def __init__(
        self,
        *,
        transaction_service: TransactionService,
    ) -> None:
        self._transaction_service = transaction_service

    def retrieve(self, *, statement_uuid: UUID, question: str) -> RetrievalResult:
        """Apply deterministic filtering and relevance ranking to transactions."""

        parsed_filters = self._extract_filters(question)
        statement_transactions = self._transaction_service.get_statement_transactions(
            statement_uuid=statement_uuid
        )

        filtered = self._filter_transactions(
            transactions=statement_transactions,
            filters=parsed_filters,
        )
        ranked = self._rank_relevance(filtered, question)

        max_records = 50
        return RetrievalResult(
            statement_uuid=statement_uuid,
            question=question,
            filters_applied=parsed_filters,
            transactions=ranked[:max_records],
        )

    def _extract_filters(self, question: str) -> dict[str, str]:
        lowered = question.lower()
        filters: dict[str, str] = {}

        month_match = re.search(
            r"\b(january|february|march|april|may|june|july|august|september|october|november|december)\b",
            lowered,
        )
        if month_match:
            month_name = month_match.group(1)
            filters["month"] = str(
                [
                    "january",
                    "february",
                    "march",
                    "april",
                    "may",
                    "june",
                    "july",
                    "august",
                    "september",
                    "october",
                    "november",
                    "december",
                ].index(month_name)
                + 1
            )

        amount_match = re.search(
            r"(?:over|above|more than|greater than)\s*\$?(\d+(?:\.\d+)?)",
            lowered,
        )
        if amount_match:
            filters["min_amount"] = amount_match.group(1)

        amount_under_match = re.search(
            r"(?:under|below|less than)\s*\$?(\d+(?:\.\d+)?)",
            lowered,
        )
        if amount_under_match:
            filters["max_amount"] = amount_under_match.group(1)

        if any(word in lowered for word in ["subscription", "recurring"]):
            filters["recurring"] = "true"

        if any(word in lowered for word in ["credit", "income", "salary", "received"]):
            filters["transaction_type"] = "credit"
        if any(word in lowered for word in ["debit", "spent", "spend", "expense"]):
            filters["transaction_type"] = "debit"

        for keyword, category in self._CATEGORY_KEYWORDS.items():
            if keyword in lowered:
                filters["category"] = category
                break

        for keyword, channel in self._PAYMENT_CHANNEL_KEYWORDS.items():
            if keyword in lowered:
                filters["payment_channel"] = channel
                break

        merchant_match = re.search(r"(?:on|at|from)\s+([a-z0-9&\-\.\s]+)\??$", lowered)
        if merchant_match:
            merchant_term = merchant_match.group(1).strip()
            if merchant_term and len(merchant_term) >= 3:
                filters["merchant"] = merchant_term

        return filters

    @staticmethod
    def _filter_transactions(
        *,
        transactions: list[TransactionDTO],
        filters: dict[str, str],
    ) -> list[TransactionDTO]:
        """Apply parsed filters to transaction records."""

        filtered = transactions

        if "month" in filters:
            month_value = int(filters["month"])
            filtered = [
                tx for tx in filtered if tx.transaction_date.month == month_value
            ]

        if "transaction_type" in filters:
            tx_type = filters["transaction_type"]
            filtered = [tx for tx in filtered if tx.transaction_type.lower() == tx_type]

        if "category" in filters:
            category = filters["category"].lower()
            filtered = [
                tx for tx in filtered if (tx.category or "").lower() == category
            ]

        if "merchant" in filters:
            merchant = filters["merchant"].lower()
            filtered = [
                tx
                for tx in filtered
                if merchant in (tx.merchant_name or "").lower()
                or merchant in tx.description.lower()
            ]

        if "payment_channel" in filters:
            channel = filters["payment_channel"].lower()
            filtered = [
                tx for tx in filtered if (tx.payment_channel or "").lower() == channel
            ]

        if "recurring" in filters:
            filtered = [
                tx for tx in filtered if bool((tx.flags or {}).get("is_recurring"))
            ]

        if "min_amount" in filters:
            threshold = Decimal(filters["min_amount"])
            filtered = [tx for tx in filtered if abs(Decimal(tx.amount)) >= threshold]

        if "max_amount" in filters:
            ceiling = Decimal(filters["max_amount"])
            filtered = [tx for tx in filtered if abs(Decimal(tx.amount)) <= ceiling]

        return filtered

    @staticmethod
    def _rank_relevance(
        transactions: list[TransactionDTO],
        question: str,
    ) -> list[TransactionDTO]:
        """Rank transactions by deterministic relevance score."""

        lowered_question = question.lower()

        def _score(tx: TransactionDTO) -> int:
            score = 0
            merchant = (tx.merchant_name or "").lower()
            category = (tx.category or "").lower()

            if merchant and merchant in lowered_question:
                score += 5
            if category and category in lowered_question:
                score += 4
            if tx.transaction_type.lower() in lowered_question:
                score += 2
            if (tx.payment_channel or "").lower() in lowered_question:
                score += 2
            score += 1 if bool((tx.flags or {}).get("is_recurring")) else 0
            return score

        return sorted(
            transactions,
            key=lambda tx: (_score(tx), tx.transaction_date, abs(Decimal(tx.amount))),
            reverse=True,
        )
