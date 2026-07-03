"""Unit tests for statement processing pipeline foundation."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

import pytest
from sqlalchemy import select

from backend.app.database.init_db import init_database
from backend.app.database.session import create_database_engine, create_session_factory
from backend.app.models.statement import Statement, StatementStatus
from backend.app.models.user import User
from walletmind.exceptions import StatementNotFoundError
from walletmind.services.statement_processing_service import StatementProcessingService
from walletmind.utils.file_uploads import detect_file_type, parser_type_for_extension


def _build_processing_service():
    database_engine = create_database_engine("sqlite+pysqlite:///:memory:")
    session_factory = create_session_factory(database_engine)
    init_database(database_engine)
    return StatementProcessingService(session_factory=session_factory), session_factory


def _create_user(session_factory) -> User:
    with session_factory() as session:
        user = User(
            full_name="Parker Lane",
            occupation="Analyst",
            monthly_income=Decimal("5500.00"),
            currency="USD",
            financial_goal="Track cashflow trends.",
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


def _create_statement(session_factory, *, user_id: int, file_type: str = "csv") -> Statement:
    with session_factory() as session:
        statement = Statement(
            user_id=user_id,
            original_filename=f"statement.{file_type}",
            stored_filename=f"{UUID('11111111-1111-1111-1111-111111111111')}.{file_type}",
            file_type=file_type,
            file_size=1024,
            status=StatementStatus.QUEUED,
        )
        session.add(statement)
        session.commit()
        session.refresh(statement)
        return statement


def test_detect_file_type_supported_values() -> None:
    assert detect_file_type(extension=".csv") == "csv"
    assert detect_file_type(extension=".xls") == "xls"
    assert detect_file_type(extension=".xlsx") == "xlsx"
    assert detect_file_type(extension=".pdf") == "pdf"
    assert detect_file_type(extension=".png") == "png"
    assert detect_file_type(extension=".jpg") == "jpg"
    assert detect_file_type(extension=".jpeg") == "jpeg"


def test_detect_file_type_unknown_value() -> None:
    assert detect_file_type(extension=".txt") == "unknown"


def test_parser_resolution_supported_values() -> None:
    assert parser_type_for_extension(".csv") == "csv"
    assert parser_type_for_extension(".xls") == "excel"
    assert parser_type_for_extension(".xlsx") == "excel"
    assert parser_type_for_extension(".pdf") == "pdf"
    assert parser_type_for_extension(".png") == "image"
    assert parser_type_for_extension(".jpg") == "image"
    assert parser_type_for_extension(".jpeg") == "image"


def test_parser_resolution_unknown_value() -> None:
    assert parser_type_for_extension(".txt") is None


def test_processing_service_status_transitions_and_timestamps(tmp_path) -> None:
    service, session_factory = _build_processing_service()
    user = _create_user(session_factory)
    statement = _create_statement(session_factory, user_id=user.id, file_type="csv")

    statement_path = tmp_path / "import.csv"
    statement_path.write_text(
        "Transaction Date,Description,Debit,Credit,Balance\n2026-01-01,Salary,0,100,100\n",
        encoding="utf-8",
    )

    service.process_statement(
        statement_uuid=statement.uuid,
        original_filename="import.csv",
        stored_file_path=str(statement_path),
        content_type="text/csv",
    )

    with session_factory() as session:
        persisted = session.scalar(select(Statement).where(Statement.uuid == statement.uuid))

    assert persisted is not None
    assert persisted.status == StatementStatus.READY_FOR_ANALYSIS
    assert persisted.bank_name is not None
    assert persisted.detected_file_type == "csv"
    assert persisted.parser_type is not None
    assert persisted.classification_confidence is not None
    assert persisted.classification_method is not None
    assert persisted.classified_at is not None
    assert persisted.processing_started_at is not None
    assert persisted.processing_completed_at is not None
    assert persisted.parsed_at is not None
    assert persisted.parsed_transaction_count >= 1
    assert persisted.direction_corrections >= 0
    assert persisted.processing_error is None


def test_processing_service_unknown_file_type_sets_unknown_parser(tmp_path) -> None:
    service, session_factory = _build_processing_service()
    user = _create_user(session_factory)
    statement = _create_statement(session_factory, user_id=user.id, file_type="txt")

    statement_path = tmp_path / "import.txt"
    statement_path.write_text("raw text", encoding="utf-8")

    service.process_statement(
        statement_uuid=statement.uuid,
        original_filename="import.txt",
        stored_file_path=str(statement_path),
        content_type="text/plain",
    )

    with session_factory() as session:
        persisted = session.scalar(select(Statement).where(Statement.uuid == statement.uuid))

    assert persisted is not None
    assert persisted.status == StatementStatus.PARSE_FAILED
    assert persisted.detected_file_type == "unknown"
    assert persisted.parser_type == "unknown"


def test_processing_service_failure_transitions_for_missing_statement() -> None:
    service, _ = _build_processing_service()

    with pytest.raises(StatementNotFoundError):
        service.process_statement(
            statement_uuid="a5e63886-61f4-4ec8-8f36-4d52a1653a4d",
            original_filename="missing.csv",
            stored_file_path="/tmp/missing.csv",
            content_type="text/csv",
        )


def test_processing_service_sets_failed_status_on_runtime_exception(monkeypatch, tmp_path) -> None:
    service, session_factory = _build_processing_service()
    user = _create_user(session_factory)
    statement = _create_statement(session_factory, user_id=user.id, file_type="csv")

    def _boom(*, original_filename: str, file_bytes: bytes, content_type: str | None = None):
        raise RuntimeError("detector crashed")

    monkeypatch.setattr(service._classifier, "classify", _boom)

    statement_path = tmp_path / "import.csv"
    statement_path.write_text("date,amount\n2026-01-01,100\n", encoding="utf-8")

    with pytest.raises(RuntimeError):
        service.process_statement(
            statement_uuid=statement.uuid,
            original_filename="import.csv",
            stored_file_path=str(statement_path),
            content_type="text/csv",
        )

    with session_factory() as session:
        persisted = session.scalar(select(Statement).where(Statement.uuid == statement.uuid))

    assert persisted is not None
    assert persisted.status == StatementStatus.FAILED
    assert persisted.processing_completed_at is not None
    assert persisted.processing_error is not None


def test_processing_service_sets_parse_failed_status_on_parser_exception(
    monkeypatch,
    tmp_path,
) -> None:
    service, session_factory = _build_processing_service()
    user = _create_user(session_factory)
    statement = _create_statement(session_factory, user_id=user.id, file_type="csv")

    def _parse_boom(*, parser_name: str, content: bytes, filename: str, content_type: str | None):
        raise RuntimeError("parser crashed")

    monkeypatch.setattr(service._parser_factory, "execute", _parse_boom)

    statement_path = tmp_path / "import.csv"
    statement_path.write_text(
        "date,description,amount\n2026-01-01,Salary,100\n",
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError):
        service.process_statement(
            statement_uuid=statement.uuid,
            original_filename="import.csv",
            stored_file_path=str(statement_path),
            content_type="text/csv",
        )

    with session_factory() as session:
        persisted = session.scalar(select(Statement).where(Statement.uuid == statement.uuid))

    assert persisted is not None
    assert persisted.status == StatementStatus.PARSE_FAILED
    assert persisted.processing_completed_at is not None
    assert persisted.processing_error is not None


def test_processing_service_sets_parse_failed_when_no_transactions_extracted(
    monkeypatch,
    tmp_path,
) -> None:
    service, session_factory = _build_processing_service()
    user = _create_user(session_factory)
    statement = _create_statement(session_factory, user_id=user.id, file_type="csv")

    def _parse_empty(*, parser_name: str, content: bytes, filename: str, content_type: str | None):
        from walletmind.schemas.transaction import ParserResultDTO

        return ParserResultDTO(
            parser_name="generic_csv_parser",
            rows_scanned=3,
            rows_skipped=3,
            transactions=[],
            errors=[],
            metadata={},
        ), type("M", (), {"duration_ms": 1})()

    monkeypatch.setattr(service._parser_factory, "execute", _parse_empty)

    statement_path = tmp_path / "import.csv"
    statement_path.write_text(
        "date,description,amount\n2026-01-01,Salary,100\n",
        encoding="utf-8",
    )

    service.process_statement(
        statement_uuid=statement.uuid,
        original_filename="import.csv",
        stored_file_path=str(statement_path),
        content_type="text/csv",
    )

    with session_factory() as session:
        persisted = session.scalar(select(Statement).where(Statement.uuid == statement.uuid))

    assert persisted is not None
    assert persisted.status == StatementStatus.PARSE_FAILED
    assert persisted.parsed_transaction_count == 0
    assert persisted.failed_transaction_count == 3
    assert persisted.processing_error is not None


def test_processing_service_axis_classification_selects_axis_parser(tmp_path) -> None:
    service, session_factory = _build_processing_service()
    user = _create_user(session_factory)
    statement = _create_statement(session_factory, user_id=user.id, file_type="csv")

    statement_path = tmp_path / "axis.csv"
    statement_path.write_text(
        "Tran Date,Particulars,CR/DR,Balance\n2026-01-01,Salary,CR,9000\n",
        encoding="utf-8",
    )

    service.process_statement(
        statement_uuid=statement.uuid,
        original_filename="axis_statement.csv",
        stored_file_path=str(statement_path),
        content_type="text/csv",
    )

    with session_factory() as session:
        persisted = session.scalar(select(Statement).where(Statement.uuid == statement.uuid))

    assert persisted is not None
    assert persisted.bank_name == "Axis Bank"
    assert persisted.parser_type == "csv_parser"


def test_processing_service_tmb_classification_selects_tmb_parser(tmp_path) -> None:
    service, session_factory = _build_processing_service()
    user = _create_user(session_factory)
    statement = _create_statement(session_factory, user_id=user.id, file_type="csv")

    statement_path = tmp_path / "tmb.csv"
    statement_path.write_text(
        "Date,Narration,Withdrawal,Deposit\n2026-01-01,ATM,250,0\n",
        encoding="utf-8",
    )

    service.process_statement(
        statement_uuid=statement.uuid,
        original_filename="tmb_statement.csv",
        stored_file_path=str(statement_path),
        content_type="text/csv",
    )

    with session_factory() as session:
        persisted = session.scalar(select(Statement).where(Statement.uuid == statement.uuid))

    assert persisted is not None
    assert persisted.bank_name == "Tamilnad Mercantile Bank"
    assert persisted.parser_type == "csv_parser"


def test_processing_service_canara_classification_selects_canara_parser(tmp_path) -> None:
    service, session_factory = _build_processing_service()
    user = _create_user(session_factory)
    statement = _create_statement(session_factory, user_id=user.id, file_type="csv")

    statement_path = tmp_path / "canara.csv"
    statement_path.write_text(
        "Txn Date,Description,Debit,Credit,Balance\n2026-01-01,UPI,250,0,1200\n",
        encoding="utf-8",
    )

    service.process_statement(
        statement_uuid=statement.uuid,
        original_filename="canara_statement.csv",
        stored_file_path=str(statement_path),
        content_type="text/csv",
    )

    with session_factory() as session:
        persisted = session.scalar(select(Statement).where(Statement.uuid == statement.uuid))

    assert persisted is not None
    assert persisted.bank_name == "Canara Bank"
    assert persisted.parser_type == "csv_parser"


def test_processing_service_excel_file_sets_excel_parser(tmp_path) -> None:
    service, session_factory = _build_processing_service()
    user = _create_user(session_factory)
    statement = _create_statement(session_factory, user_id=user.id, file_type="xlsx")

    statement_path = tmp_path / "axis.xlsx"
    statement_path.write_text(
        "Tran Date,Particulars,CR/DR,Balance\n2026-01-01,Salary,CR,9000\n",
        encoding="utf-8",
    )

    service.process_statement(
        statement_uuid=statement.uuid,
        original_filename="axis_statement.xlsx",
        stored_file_path=str(statement_path),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    with session_factory() as session:
        persisted = session.scalar(select(Statement).where(Statement.uuid == statement.uuid))

    assert persisted is not None
    assert persisted.parser_type == "excel_parser"


def test_processing_service_pdf_file_sets_pdf_parser(tmp_path) -> None:
    service, session_factory = _build_processing_service()
    user = _create_user(session_factory)
    statement = _create_statement(session_factory, user_id=user.id, file_type="pdf")

    statement_path = tmp_path / "axis.pdf"
    statement_path.write_text(
        "Axis Bank Statement\n01/01/2026  Salary  1000.00\n",
        encoding="utf-8",
    )

    service.process_statement(
        statement_uuid=statement.uuid,
        original_filename="axis_statement.pdf",
        stored_file_path=str(statement_path),
        content_type="application/pdf",
    )

    with session_factory() as session:
        persisted = session.scalar(select(Statement).where(Statement.uuid == statement.uuid))

    assert persisted is not None
    assert persisted.parser_type == "pdf_parser"
