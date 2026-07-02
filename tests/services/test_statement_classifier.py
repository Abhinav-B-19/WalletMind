"""Unit tests for statement classification components."""

from __future__ import annotations

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


def test_axis_detection() -> None:
    detector = BankDetector()
    inspection = _inspect_csv(
        "axis_statement.csv",
        "Tran Date,Particulars,CR/DR,Balance\n2026-01-01,Credit Salary,CR,2000",
    )
    decision = detector.detect(inspection)

    assert decision.bank_name == "Axis Bank"
    assert decision.confidence > 0.2
    assert "header-keyword" in decision.method or "column-name" in decision.method


def test_tmb_detection() -> None:
    detector = BankDetector()
    inspection = _inspect_csv(
        "tmb_statement.csv",
        "Date,Narration,Withdrawal,Deposit\n2026-01-01,ATM,-200,0",
    )
    decision = detector.detect(inspection)

    assert decision.bank_name == "Tamilnad Mercantile Bank (TMB)"
    assert decision.confidence > 0.2


def test_canara_detection() -> None:
    detector = BankDetector()
    inspection = _inspect_csv(
        "canara_statement.csv",
        "Txn Date,Description,Debit,Credit,Balance\n2026-01-01,UPI,200,0,800",
    )
    decision = detector.detect(inspection)

    assert decision.bank_name == "Canara Bank"
    assert decision.confidence > 0.2


def test_unknown_detection() -> None:
    detector = BankDetector()
    inspection = _inspect_csv(
        "mystery_statement.csv",
        "A,B,C\n1,2,3",
    )
    decision = detector.detect(inspection)

    assert decision.bank_name == "Unknown"
    assert decision.confidence == 0.0
    assert decision.unknown_reason is not None


def test_parser_resolver() -> None:
    resolver = ParserResolver()

    assert resolver.resolve(bank_name="Axis Bank", detected_file_type="xlsx") == "axis_excel_parser"
    assert (
        resolver.resolve(
            bank_name="Tamilnad Mercantile Bank (TMB)",
            detected_file_type="csv",
        )
        == "tmb_excel_parser"
    )
    assert resolver.resolve(bank_name="Canara Bank", detected_file_type="xls") == "canara_excel_parser"
    assert resolver.resolve(bank_name="Unknown", detected_file_type="xlsx") == "generic_excel_parser"
    assert resolver.resolve(bank_name="Unknown", detected_file_type="pdf") == "generic_pdf_parser"
    assert resolver.resolve(bank_name="Unknown", detected_file_type="png") == "ocr_pipeline"


def test_confidence_scoring_higher_for_stronger_matches() -> None:
    detector = BankDetector()

    strong = _inspect_csv(
        "axis_statement.csv",
        "Tran Date,Particulars,CR/DR,Balance\n2026-01-01,Credit Salary,CR,2000",
    )
    weak = _inspect_csv("axis_statement.csv", "col1,col2\n1,2")

    strong_score = detector.detect(strong).confidence
    weak_score = detector.detect(weak).confidence
    assert strong_score >= weak_score


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
    )

    decision = detector.detect(inspection)

    assert decision.bank_name == "Axis Bank"
    assert "sheet-name" in decision.method