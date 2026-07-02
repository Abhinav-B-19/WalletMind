"""Statement classification pipeline components."""

from __future__ import annotations

from dataclasses import dataclass
import csv
from io import StringIO
from pathlib import Path
from time import perf_counter

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


class BankDetector:
    """Determines target institution using multi-signal weighted heuristics."""

    _SIGNALS: dict[str, dict[str, tuple[str, ...]]] = {
        "Axis Bank": {
            "sheet": ("axis",),
            "header": ("particulars", "tran date", "balance", "cr/dr"),
            "column": ("particulars", "tran date", "balance", "cr/dr"),
            "rows": ("axis",),
            "filename": ("axis",),
        },
        "Tamilnad Mercantile Bank (TMB)": {
            "sheet": ("tmb", "tamilnad"),
            "header": ("date", "narration", "withdrawal", "deposit"),
            "column": ("date", "narration", "withdrawal", "deposit"),
            "rows": ("tmb", "tamilnad"),
            "filename": ("tmb", "tamilnad"),
        },
        "Canara Bank": {
            "sheet": ("canara",),
            "header": ("txn date", "description", "debit", "credit", "balance"),
            "column": ("txn date", "description", "debit", "credit", "balance"),
            "rows": ("canara",),
            "filename": ("canara",),
        },
    }

    _WEIGHTS = {
        "sheet": 0.35,
        "header": 0.25,
        "column": 0.2,
        "rows": 0.1,
        "filename": 0.07,
        "metadata": 0.03,
    }

    def detect(self, inspection: FileInspectionResult) -> DetectionDecision:
        best_bank = "Unknown"
        best_score = 0.0
        best_method = "fallback:unknown"

        filename = inspection.filename.lower()
        row_blob = " ".join(inspection.sample_rows).lower()
        metadata_blob = " ".join(inspection.metadata_signals).lower()

        for bank_name, rules in self._SIGNALS.items():
            score = 0.0
            methods: list[str] = []

            sheet_ratio = self._match_ratio(inspection.sheet_names, rules["sheet"])
            if sheet_ratio > 0:
                score += self._WEIGHTS["sheet"] * sheet_ratio
                methods.append("sheet-name")

            header_ratio = self._match_ratio(inspection.header_keywords, rules["header"])
            if header_ratio > 0:
                score += self._WEIGHTS["header"] * header_ratio
                methods.append("header-keyword")

            column_ratio = self._match_ratio(inspection.columns, rules["column"])
            if column_ratio > 0:
                score += self._WEIGHTS["column"] * column_ratio
                methods.append("column-name")

            row_ratio = self._match_ratio((row_blob,), rules["rows"])
            if row_ratio > 0:
                score += self._WEIGHTS["rows"] * row_ratio
                methods.append("row-sample")

            filename_ratio = self._match_ratio((filename,), rules["filename"])
            if filename_ratio > 0:
                score += self._WEIGHTS["filename"] * filename_ratio
                methods.append("filename")

            metadata_ratio = self._match_ratio((metadata_blob,), rules["filename"])
            if metadata_ratio > 0:
                score += self._WEIGHTS["metadata"] * metadata_ratio
                methods.append("metadata")

            if score > best_score:
                best_score = score
                best_bank = bank_name
                best_method = " + ".join(methods) if methods else "fallback"

        if best_score < 0.2:
            return DetectionDecision(
                bank_name="Unknown",
                confidence=0.0,
                method="fallback:unknown",
                unknown_reason="Insufficient known bank signals in sheet/header/rows/filename.",
            )

        confidence = min(0.99, round(best_score, 2))
        return DetectionDecision(
            bank_name=best_bank,
            confidence=confidence,
            method=best_method,
            unknown_reason=None,
        )

    @staticmethod
    def _match_ratio(haystack: tuple[str, ...], needles: tuple[str, ...]) -> float:
        if not needles:
            return 0.0
        haystack_blob = " ".join(item.lower() for item in haystack)
        matched = sum(1 for needle in needles if needle.lower() in haystack_blob)
        return matched / len(needles)


class ParserResolver:
    """Resolves parser implementation key from file type and detected bank."""

    _BANK_FORMAT_PARSERS = {
        ("Axis Bank", "xls"): "axis_excel_parser",
        ("Axis Bank", "xlsx"): "axis_excel_parser",
        ("Axis Bank", "csv"): "axis_excel_parser",
        ("Tamilnad Mercantile Bank (TMB)", "xls"): "tmb_excel_parser",
        ("Tamilnad Mercantile Bank (TMB)", "xlsx"): "tmb_excel_parser",
        ("Tamilnad Mercantile Bank (TMB)", "csv"): "tmb_excel_parser",
        ("Canara Bank", "xls"): "canara_excel_parser",
        ("Canara Bank", "xlsx"): "canara_excel_parser",
        ("Canara Bank", "csv"): "canara_excel_parser",
    }

    _GENERIC_FORMAT_PARSERS = {
        "xls": "generic_excel_parser",
        "xlsx": "generic_excel_parser",
        "csv": "generic_excel_parser",
        "pdf": "generic_pdf_parser",
        "png": "ocr_pipeline",
        "jpg": "ocr_pipeline",
        "jpeg": "ocr_pipeline",
        "ofx": "generic_ofx_parser",
        "qif": "generic_qif_parser",
        "zip": "archive_classifier",
        "unknown": "unknown",
    }

    def resolve(self, *, bank_name: str, detected_file_type: str) -> str:
        specific = self._BANK_FORMAT_PARSERS.get((bank_name, detected_file_type))
        if specific:
            return specific
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
