"""Bank detection service using deterministic keyword matching."""

from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class BankDetectionResult:
    bank_name: str
    confidence: float
    method: str


class BankDetectionService:
    """Detects bank name from metadata/content hints without AI/OCR."""

    _BANK_KEYWORDS: dict[str, tuple[str, ...]] = {
        "Axis Bank": ("axis bank", "axis"),
        "HDFC Bank": ("hdfc",),
        "ICICI Bank": ("icici",),
        "State Bank of India": ("state bank", "sbi"),
        "Tamilnad Mercantile Bank": ("tamilnad mercantile", "tmb"),
        "Canara Bank": ("canara",),
        "Indian Bank": ("indian bank",),
        "IDFC First Bank": ("idfc",),
        "Kotak Mahindra Bank": ("kotak",),
        "YES Bank": ("yes bank",),
    }

    def detect_bank(
        self,
        *,
        metadata_text: str | None = None,
        header_text: str | None = None,
        worksheet_title: str | None = None,
        csv_headers: list[str] | tuple[str, ...] | None = None,
        filename: str | None = None,
    ) -> BankDetectionResult:
        sources = [
            ("metadata", self._normalize(metadata_text)),
            ("pdf_header", self._normalize(header_text)),
            ("worksheet", self._normalize(worksheet_title)),
            ("csv_header", self._normalize(" ".join(csv_headers or []))),
            ("filename", self._normalize(filename)),
        ]

        for source_name, source_text in sources:
            if not source_text:
                continue
            matched_bank = self._match_bank(source_text)
            if matched_bank is None:
                continue
            confidence = 0.9 if source_name in {"metadata", "pdf_header", "worksheet"} else 0.75
            if source_name == "filename":
                confidence = 0.65
            return BankDetectionResult(
                bank_name=matched_bank,
                confidence=confidence,
                method=source_name,
            )

        return BankDetectionResult(
            bank_name="Unknown",
            confidence=0.0,
            method="fallback:unknown",
        )

    def _match_bank(self, text: str) -> str | None:
        for bank_name, keywords in self._BANK_KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                return bank_name
        return None

    @staticmethod
    def _normalize(value: str | None) -> str:
        if not value:
            return ""
        text = value.lower()
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()
