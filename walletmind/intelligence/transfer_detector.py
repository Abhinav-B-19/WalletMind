"""Deterministic transfer detector."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TransferDetectionResult:
    is_transfer: bool
    is_internal_transfer: bool


class TransferDetector:
    """Detects transfer and internal transfer semantics."""

    _TRANSFER_KEYWORDS = (
        "self transfer",
        "internal transfer",
        "account transfer",
        "transfer to",
        "to self",
        "own account",
        "same account",
        "neft transfer",
        "imps transfer",
        "rtgs transfer",
    )

    _INTERNAL_KEYWORDS = (
        "self",
        "own account",
        "same account",
        "to self",
        "internal",
    )

    def detect(self, *, narration: str, description: str, merchant_name: str | None, account_holder_name: str | None) -> TransferDetectionResult:
        haystack = f"{narration} {description} {merchant_name or ''}".lower()
        is_transfer = any(keyword in haystack for keyword in self._TRANSFER_KEYWORDS)

        is_internal = any(keyword in haystack for keyword in self._INTERNAL_KEYWORDS)
        if account_holder_name:
            owner = " ".join(account_holder_name.split()).strip().lower()
            if owner and owner in haystack:
                is_internal = True

        return TransferDetectionResult(is_transfer=is_transfer, is_internal_transfer=is_internal)
