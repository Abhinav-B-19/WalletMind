"""Statement classification pipeline components."""

from __future__ import annotations

from dataclasses import dataclass
import csv
from io import StringIO
from pathlib import Path
from time import perf_counter
from typing import Any

from walletmind.services.bank_detection_service import BankDetectionService
from walletmind.utils.file_uploads import detect_file_type


@dataclass(frozen=True)
class ClassificationResult:
    """Immutable statement classification output."""

    detected_bank: str
    statement_format: str
    detected_file_type: str
    parser_type: str
    confidence: float
    classification_method: str
    should_continue: bool
    unknown_reason: str | None = None


@dataclass(frozen=True)
class FileInspectionResult:
    """Signals extracted from raw file payload for classification."""

    file_extension: str
    detected_file_type: str
    filename: str
    sheet_names: tuple[str, ...]
    header_keywords: tuple[str, ...]
    columns: tuple[str, ...]
    sample_rows: tuple[str, ...]
    metadata_signals: tuple[str, ...]
    header_text: str


@dataclass(frozen=True)
class DetectionDecision:
    """Intermediate bank detection decision."""

    bank_name: str
    confidence: float
    method: str
    unknown_reason: str | None = None


class FileInspector:
    """Extracts classification signals from statement files without parsing transactions."""

    def inspect(
        self,
        *,
        original_filename: str,
        file_bytes: bytes,
        content_type: str | None = None,
    ) -> FileInspectionResult:
        extension = Path(original_filename).suffix.lower()
        detected_type = detect_file_type(extension=extension, content_type=content_type)

        sheet_names = self._extract_sheet_names(file_bytes=file_bytes, extension=extension)
        header_keywords, columns, sample_rows = self._extract_text_signals(
            file_bytes=file_bytes,
            extension=extension,
        )
        header_text = self._extract_pdf_header_text(file_bytes=file_bytes, extension=extension)

        metadata_signals = tuple(
            signal
            for signal in (
                f"extension:{extension}",
                f"mime:{(content_type or '').lower()}",
            )
            if signal.split(":", maxsplit=1)[1]
        )

        return FileInspectionResult(
            file_extension=extension,
            detected_file_type=detected_type,
            filename=Path(original_filename).name,
            sheet_names=sheet_names,
            header_keywords=header_keywords,
            columns=columns,
            sample_rows=sample_rows,
            metadata_signals=metadata_signals,
            header_text=header_text,
        )

    @staticmethod
    def _extract_sheet_names(*, file_bytes: bytes, extension: str) -> tuple[str, ...]:
        if extension not in {".xls", ".xlsx"}:
            return tuple()

        text = file_bytes.decode("utf-8", errors="ignore")
        # Lightweight heuristic: embedded worksheet names in zipped XML or legacy text dumps.
        candidates = []
        for token in (
            "axis",
            "canara",
            "tmb",
            "tamilnad",
            "statement",
            "transactions",
        ):
            if token in text.lower():
                candidates.append(token)
        return tuple(candidates)

    @staticmethod
    def _extract_text_signals(
        *,
        file_bytes: bytes,
        extension: str,
    ) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
        if extension in {".png", ".jpg", ".jpeg", ".pdf"}:
            return tuple(), tuple(), tuple()

        decoded = file_bytes.decode("utf-8", errors="ignore")
        if not decoded.strip():
            return tuple(), tuple(), tuple()

        rows = []
        try:
            reader = csv.reader(StringIO(decoded))
            for index, row in enumerate(reader):
                if index >= 30:
                    break
                rows.append([cell.strip() for cell in row])
        except csv.Error:
            return tuple(), tuple(), tuple()

        if not rows:
            return tuple(), tuple(), tuple()

        header = rows[0]
        header_keywords = tuple(cell.lower() for cell in header if cell)
        columns = tuple(header_keywords)
        sample_rows = tuple(
            " | ".join(cell for cell in row if cell)
            for row in rows[1:30]
            if any(row)
        )
        return header_keywords, columns, sample_rows

    @staticmethod
    def _extract_pdf_header_text(*, file_bytes: bytes, extension: str) -> str:
        if extension != ".pdf":
            return ""
        decoded = file_bytes.decode("utf-8", errors="ignore")
        lines = [line.strip() for line in decoded.splitlines() if line.strip()]
        return " ".join(lines[:10])


class BankDetector:
    """Determines target institution using multi-signal weighted heuristics."""

    def __init__(self, *, detector: BankDetectionService | None = None) -> None:
        self._detector = detector or BankDetectionService()

    def detect(self, inspection: FileInspectionResult) -> DetectionDecision:
        decision = self._detector.detect_bank(
            metadata_text=" ".join(inspection.metadata_signals),
            header_text=inspection.header_text,
            worksheet_title=" ".join(inspection.sheet_names),
            csv_headers=list(inspection.header_keywords or inspection.columns),
            filename=inspection.filename,
        )

        if decision.bank_name == "Unknown":
            return DetectionDecision(
                bank_name="Unknown",
                confidence=0.0,
                method="fallback:unknown",
                unknown_reason="Insufficient known bank signals in document metadata/header/sheet/csv/filename.",
            )

        return DetectionDecision(
            bank_name=decision.bank_name,
            confidence=decision.confidence,
            method=decision.method,
            unknown_reason=None,
        )


class ParserResolver:
    """Resolves parser implementation key from file type and detected bank."""

    _GENERIC_FORMAT_PARSERS = {
        "xls": "excel_parser",
        "xlsx": "excel_parser",
        "csv": "csv_parser",
        "pdf": "pdf_parser",
        "png": "ocr_parser",
        "jpg": "ocr_parser",
        "jpeg": "ocr_parser",
        "unknown": "unknown",
    }

    def resolve(self, *, bank_name: str, detected_file_type: str) -> str:
        return self._GENERIC_FORMAT_PARSERS.get(detected_file_type, "unknown")


class StatementClassifier:
    """Coordinates file inspection, bank detection, and parser resolution."""

    def __init__(
        self,
        *,
        file_inspector: FileInspector,
        bank_detector: BankDetector,
        parser_resolver: ParserResolver,
    ) -> None:
        self._file_inspector = file_inspector
        self._bank_detector = bank_detector
        self._parser_resolver = parser_resolver

    def classify(
        self,
        *,
        original_filename: str,
        file_bytes: bytes,
        content_type: str | None = None,
    ) -> ClassificationResult:
        started = perf_counter()

        inspection = self._file_inspector.inspect(
            original_filename=original_filename,
            file_bytes=file_bytes,
            content_type=content_type,
        )

        decision = self._bank_detector.detect(inspection)
        parser_type = self._parser_resolver.resolve(
            bank_name=decision.bank_name,
            detected_file_type=inspection.detected_file_type,
        )

        method = f"{decision.method};duration_ms={int((perf_counter() - started) * 1000)}"

        return ClassificationResult(
            detected_bank=decision.bank_name,
            statement_format=inspection.file_extension.lstrip(".") or "unknown",
            detected_file_type=inspection.detected_file_type,
            parser_type=parser_type,
            confidence=decision.confidence,
            classification_method=method,
            should_continue=True,
            unknown_reason=decision.unknown_reason,
        )
