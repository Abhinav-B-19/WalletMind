"""Deterministic transaction normalization and enrichment engine."""

from __future__ import annotations

from dataclasses import dataclass
import re

from walletmind.schemas.transaction import TransactionCreateDTO


@dataclass
class EnrichedTransaction:
    """Enriched transaction values ready for persistence."""

    raw_description: str
    clean_description: str
    merchant_name: str | None
    bank_gateway: str | None
    category: str
    normalized_transaction_type: str
    is_internal_transfer: bool
    is_income: bool
    is_expense: bool


class TransactionNormalizer:
    """Deterministic normalization pipeline for parsed transactions."""

    _PROTOCOL_STOP_WORDS = {
        "upi",
        "p2m",
        "p2a",
        "imps",
        "neft",
        "rtgs",
        "ach",
        "cr",
        "dr",
        "debit",
        "credit",
        "transfer",
        "self",
        "bank",
        "limited",
        "ltd",
        "yes",
        "axis",
        "hdfc",
        "icici",
        "sbi",
        "canara",
        "tmb",
        "india",
        "payment",
        "pay",
        "txn",
        "transaction",
    }

    _BANK_GATEWAY_PHRASES = (
        "yes bank",
        "yes bank limited",
        "axis bank",
        "hdfc bank",
        "hdfc bank ltd",
        "icici bank",
        "state bank of india",
        "sbi",
        "utib",
        "idib",
        "cnrb",
        "tmb",
        "kvbl",
        "iob",
        "bob",
    )

    _DESCRIPTION_DICTIONARY: dict[str, str] = {
        "haircu": "Haircut",
        "subscrip": "Subscription",
        "petrol": "Petrol",
        "upi juspay": "UPI Payment",
        "paid v": "Investment",
    }

    _INCOME_KEYWORDS = {
        "salary",
        "payroll",
        "salary credit",
        "neft salary",
    }

    _TRANSFER_KEYWORDS = {
        "upi self",
        "self transfer",
        "own account",
        "same account",
        "transfer to self",
        "internal transfer",
    }

    _CATEGORY_RULES: list[tuple[str, set[str]]] = [
        ("Transfer", {"transfer", "self transfer", "upi self", "own account", "same account"}),
        ("Income", {"salary", "payroll", "salary credit", "neft salary"}),
        ("Fuel", {"petrol", "fuel", "diesel"}),
        ("Food & Dining", {"swiggy", "zomato", "restaurant", "hotel", "food"}),
        ("Shopping", {"amazon", "flipkart", "shopping"}),
        ("Investments", {"groww", "zerodha", "mutual", "sip"}),
        ("Entertainment", {"netflix", "spotify", "hotstar", "youtube"}),
        ("Utilities", {"electricity", "water", "gas", "broadband"}),
        ("Healthcare", {"hospital", "clinic", "medical", "pharmacy"}),
        ("Transport", {"uber", "ola", "metro", "rail"}),
    ]

    def enrich(
        self,
        *,
        transaction: TransactionCreateDTO,
        account_holder_name: str | None,
    ) -> EnrichedTransaction:
        """Run deterministic enrichment pipeline over a parsed transaction."""

        raw_description = transaction.description.strip()
        segments = self._candidate_segments(raw_description)
        bank_gateway = self._extract_bank_gateway(segments)
        merchant_name = self._extract_merchant(segments)
        clean_description = self._clean_description(segments, merchant_name)

        is_internal_transfer = self._is_internal_transfer(
            raw_description=raw_description,
            clean_description=clean_description,
            account_holder_name=account_holder_name,
        )
        is_income = self._is_income(
            raw_description=raw_description,
            clean_description=clean_description,
        )
        is_expense = self._is_expense(
            transaction_type=transaction.transaction_type,
            amount=transaction.amount,
            is_internal_transfer=is_internal_transfer,
        )

        normalized_type = self._normalized_transaction_type(
            is_internal_transfer=is_internal_transfer,
            is_income=is_income,
            is_expense=is_expense,
        )

        category = self._category(
            raw_description=raw_description,
            clean_description=clean_description,
            merchant_name=merchant_name,
            normalized_transaction_type=normalized_type,
        )

        return EnrichedTransaction(
            raw_description=raw_description,
            clean_description=clean_description,
            merchant_name=merchant_name,
            bank_gateway=bank_gateway,
            category=category,
            normalized_transaction_type=normalized_type,
            is_internal_transfer=is_internal_transfer,
            is_income=is_income,
            is_expense=is_expense,
        )

    def _extract_merchant(self, segments: list[str]) -> str | None:
        if not segments:
            return None

        for segment in segments:
            normalized = segment.lower()
            words = [word for word in re.split(r"\s+", normalized) if word]
            if not words:
                continue
            if self._is_protocol_segment(normalized):
                continue
            if self._is_reference_segment(normalized):
                continue
            if self._is_bank_gateway_segment(normalized):
                continue
            if len(segment) < 3:
                continue
            return self._normalize_spaces(segment)
        return None

    def _clean_description(self, segments: list[str], merchant_name: str | None) -> str:
        if not segments:
            return ""

        merchant_key = (merchant_name or "").strip().lower()
        fallback_description: str | None = None
        for segment in segments:
            normalized = self._normalize_spaces(segment)
            normalized_key = normalized.lower()
            if not normalized_key:
                continue
            if normalized_key == merchant_key:
                continue
            if self._is_protocol_segment(normalized_key):
                continue
            if self._is_reference_segment(normalized_key):
                continue
            if self._is_bank_gateway_segment(normalized_key):
                continue

            mapped = self._normalize_description_from_segment(normalized)
            if mapped is not None:
                return mapped

            if len(normalized_key) <= 40 and len(normalized_key.split()) <= 4:
                if fallback_description is None:
                    fallback_description = normalized.title()

        if fallback_description is not None:
            return fallback_description

        if merchant_name:
            return merchant_name.title() if merchant_name.isupper() else merchant_name

        fallback = self._normalize_spaces(segments[0])
        mapped_fallback = self._normalize_description_from_segment(fallback)
        return mapped_fallback if mapped_fallback is not None else fallback.title()

    def _extract_bank_gateway(self, segments: list[str]) -> str | None:
        for segment in segments:
            normalized = self._normalize_spaces(segment).lower()
            if self._is_bank_gateway_segment(normalized):
                return self._normalize_spaces(segment)
        return None

    def _normalize_description_from_segment(self, segment: str) -> str | None:
        normalized = self._normalize_spaces(segment).lower()
        if not normalized:
            return None

        for key, value in self._DESCRIPTION_DICTIONARY.items():
            if key in normalized:
                return value

        return None

    @staticmethod
    def _normalize_spaces(segment: str) -> str:
        return re.sub(r"\s+", " ", segment).strip(" .,_-")

    def _is_protocol_segment(self, normalized_segment: str) -> bool:
        words = [word for word in re.split(r"\s+", normalized_segment) if word]
        if not words:
            return True
        return all(word in self._PROTOCOL_STOP_WORDS for word in words)

    @staticmethod
    def _is_reference_segment(normalized_segment: str) -> bool:
        return re.fullmatch(r"[0-9\-]+", normalized_segment) is not None

    def _is_bank_gateway_segment(self, normalized_segment: str) -> bool:
        if "bank" in normalized_segment:
            return True
        return any(phrase in normalized_segment for phrase in self._BANK_GATEWAY_PHRASES)

    def _candidate_segments(self, raw_description: str) -> list[str]:
        flattened = re.sub(r"[|]", "/", raw_description)
        flattened = re.sub(r"\s+-\s+", "/", flattened)
        pieces = [piece.strip() for piece in re.split(r"[/:]+", flattened)]
        cleaned = [self._normalize_spaces(piece) for piece in pieces]
        return [piece for piece in cleaned if piece]

    def _is_internal_transfer(
        self,
        *,
        raw_description: str,
        clean_description: str,
        account_holder_name: str | None,
    ) -> bool:
        haystack = f"{raw_description} {clean_description}".lower()
        if any(keyword in haystack for keyword in self._TRANSFER_KEYWORDS):
            return True

        if account_holder_name:
            owner = re.sub(r"\s+", " ", account_holder_name).strip().lower()
            if owner and owner in haystack:
                return True

        return False

    def _is_income(self, *, raw_description: str, clean_description: str) -> bool:
        haystack = f"{raw_description} {clean_description}".lower()
        return any(keyword in haystack for keyword in self._INCOME_KEYWORDS)

    @staticmethod
    def _is_expense(
        *,
        transaction_type: str,
        amount,
        is_internal_transfer: bool,
    ) -> bool:
        if is_internal_transfer:
            return False
        if str(transaction_type).lower() == "debit":
            return True
        return amount < 0

    @staticmethod
    def _normalized_transaction_type(
        *,
        is_internal_transfer: bool,
        is_income: bool,
        is_expense: bool,
    ) -> str:
        if is_internal_transfer:
            return "internal_transfer"
        if is_income:
            return "income"
        if is_expense:
            return "expense"
        return "other"

    def _category(
        self,
        *,
        raw_description: str,
        clean_description: str,
        merchant_name: str | None,
        normalized_transaction_type: str,
    ) -> str:
        if normalized_transaction_type == "internal_transfer":
            return "Transfer"

        haystack = " ".join(
            part for part in [raw_description, clean_description, merchant_name or ""] if part
        ).lower()

        for category, keywords in self._CATEGORY_RULES:
            if any(keyword in haystack for keyword in keywords):
                return category

        return "Others"