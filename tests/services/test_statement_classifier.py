"""Unit tests for statement classification components."""

from __future__ import annotations

from walletmind.services.bank_detection_service import BankDetectionService
from walletmind.services.statement_classifier import (
    BankDetector,
    FileInspector,
    FileInspectionResult,
    ParserResolver,
)


def _inspect_csv(filename: str, content: str):
    inspector = FileInspector()
    return inspector.inspect(
        original_filename=filename,
        file_bytes=content.encode("utf-8"),
        content_type="text/csv",
    )


def test_axis_detection_from_filename_hint() -> None:
    service = BankDetectionService()
    result = service.detect_bank(filename="Axis_Statement.csv")

    assert result.bank_name == "Axis Bank"
    assert result.method == "filename"


def test_axis_detection_from_csv_header() -> None:
    service = BankDetectionService()
    result = service.detect_bank(
        csv_headers=["Tran Date", "Particulars", "Axis Salary Credit"],
    )

    assert result.bank_name == "Axis Bank"
    assert result.method == "csv_header"


def test_document_content_wins_over_filename_hint() -> None:
    service = BankDetectionService()
    result = service.detect_bank(
        metadata_text="HDFC Bank Account Statement",
        filename="axis_statement.csv",
    )

    assert result.bank_name == "HDFC Bank"
    assert result.method == "metadata"


def test_unknown_detection_fallback() -> None:
    service = BankDetectionService()
    result = service.detect_bank(
        metadata_text="",
        header_text="",
        worksheet_title="",
        csv_headers=["date", "description", "amount"],
        filename="statement.csv",
    )

    assert result.bank_name == "Unknown"
    assert result.confidence == 0.0


def test_parser_resolver() -> None:
    resolver = ParserResolver()

    assert resolver.resolve(bank_name="Axis Bank", detected_file_type="csv") == "csv_parser"
    assert resolver.resolve(bank_name="Unknown", detected_file_type="xlsx") == "excel_parser"
    assert resolver.resolve(bank_name="Unknown", detected_file_type="xls") == "excel_parser"
    assert resolver.resolve(bank_name="Unknown", detected_file_type="pdf") == "pdf_parser"
    assert resolver.resolve(bank_name="Unknown", detected_file_type="png") == "ocr_parser"


def test_detector_uses_filename_when_no_content_signals() -> None:
    detector = BankDetector()
    inspection = _inspect_csv(
        "canara_may.xlsx.csv",
        "col1,col2\n1,2",
    )
    decision = detector.detect(inspection)

    assert decision.bank_name == "Canara Bank"
    assert decision.method == "filename"


def test_file_inspector_extracts_signals() -> None:
    inspection = _inspect_csv(
        "axis_statement.csv",
        "Tran Date,Particulars,CR/DR,Balance\n2026-01-01,Credit Salary,CR,2000",
    )

    assert inspection.file_extension == ".csv"
    assert inspection.detected_file_type == "csv"
    assert "tran date" in inspection.header_keywords
    assert "particulars" in inspection.columns
    assert len(inspection.sample_rows) >= 1
    assert inspection.header_text == ""


def test_file_inspector_handles_image_without_tabular_signals() -> None:
    inspector = FileInspector()
    inspection = inspector.inspect(
        original_filename="receipt.png",
        file_bytes=b"\x89PNG\r\n\x1a\n",
        content_type="image/png",
    )

    assert inspection.detected_file_type == "png"
    assert inspection.header_keywords == tuple()
    assert inspection.columns == tuple()
    assert inspection.sample_rows == tuple()
    assert inspection.header_text == ""


def test_bank_detector_uses_sheet_name_signal() -> None:
    detector = BankDetector()
    inspection = FileInspectionResult(
        file_extension=".xlsx",
        detected_file_type="xlsx",
        filename="statement.xlsx",
        sheet_names=("axis", "transactions"),
        header_keywords=tuple(),
        columns=tuple(),
        sample_rows=tuple(),
        metadata_signals=tuple(),
        header_text="",
    )

    decision = detector.detect(inspection)

    assert decision.bank_name == "Axis Bank"
    assert decision.method == "worksheet"