"""Deterministic merchant and gateway detector."""

from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class MerchantDetectionResult:
    merchant_name: str | None
    bank_gateway: str | None


class MerchantDetector:
    """Extracts merchant and bank/gateway from narration using fixed rules."""

    _PROTOCOL_TOKENS = {
        "upi",
        "p2m",
        "p2a",
        "imps",
        "neft",
        "rtgs",
        "ach",
        "txn",
        "transaction",
        "transfer",
        "dr",
        "cr",
        "debit",
        "credit",
    }

    _BANK_GATEWAY_PATTERNS = (
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
        "bank",
    )

    _MERCHANT_ALIASES: tuple[tuple[str, str], ...] = (
        ("swiggy", "Swiggy"),
        ("zomato", "Zomato"),
        ("google in", "Google Play"),
        ("google play", "Google Play"),
        ("amazon seller services", "Amazon"),
        ("amazon", "Amazon"),
        ("netflix", "Netflix"),
        ("spotify", "Spotify"),
        ("bp petrol pump", "BP Petrol Pump"),
        ("indian oil", "Indian Oil"),
        ("groww invest tech pvt", "Groww Invest Tech Pvt"),
    )

    def detect(self, *, narration: str) -> MerchantDetectionResult:
        segments = self._segments(narration)
        bank_gateway = self._detect_bank_gateway(segments)

        merchant: str | None = None
        for segment in segments:
            key = segment.lower()
            if self._is_protocol_segment(key) or self._is_reference_segment(key):
                continue
            if self._is_bank_gateway_segment(key):
                continue
            alias = self._resolve_alias(segment)
            merchant = alias if alias is not None else self._title(segment)
            break

        return MerchantDetectionResult(merchant_name=merchant, bank_gateway=bank_gateway)

    @staticmethod
    def _title(value: str) -> str:
        if value.isupper():
            return value.title()
        return value

    def _resolve_alias(self, segment: str) -> str | None:
        key = segment.lower()
        for needle, canonical in self._MERCHANT_ALIASES:
            if needle in key:
                return canonical
        return None

    def _detect_bank_gateway(self, segments: list[str]) -> str | None:
        for segment in segments:
            if self._is_bank_gateway_segment(segment.lower()):
                return segment
        return None

    def _is_bank_gateway_segment(self, segment: str) -> bool:
        return any(token in segment for token in self._BANK_GATEWAY_PATTERNS)

    def _is_protocol_segment(self, segment: str) -> bool:
        words = [token for token in segment.split(" ") if token]
        return bool(words) and all(token in self._PROTOCOL_TOKENS for token in words)

    @staticmethod
    def _is_reference_segment(segment: str) -> bool:
        return re.fullmatch(r"[0-9\-]+", segment) is not None

    def _segments(self, narration: str) -> list[str]:
        flattened = re.sub(r"[|]", "/", narration)
        flattened = re.sub(r"\s+-\s+", "/", flattened)
        pieces = [piece.strip() for piece in re.split(r"[/:]+", flattened)]
        cleaned = [re.sub(r"\s+", " ", piece).strip(" .,_-") for piece in pieces]
        return [piece for piece in cleaned if piece]
