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


def test_processing_service_status_transitions_and_timestamps() -> None:
    service, session_factory = _build_processing_service()
    user = _create_user(session_factory)
    statement = _create_statement(session_factory, user_id=user.id, file_type="csv")

    service.process_statement(
        statement_uuid=statement.uuid,
        original_filename="import.csv",
        content_type="text/csv",
    )

    with session_factory() as session:
        persisted = session.scalar(select(Statement).where(Statement.uuid == statement.uuid))

    assert persisted is not None
    assert persisted.status == StatementStatus.READY_FOR_PARSING
    assert persisted.detected_file_type == "csv"
    assert persisted.parser_type == "csv"
    assert persisted.processing_started_at is not None
    assert persisted.processing_completed_at is not None
    assert persisted.processing_error is None


def test_processing_service_unknown_file_type_sets_unknown_parser() -> None:
    service, session_factory = _build_processing_service()
    user = _create_user(session_factory)
    statement = _create_statement(session_factory, user_id=user.id, file_type="txt")

    service.process_statement(
        statement_uuid=statement.uuid,
        original_filename="import.txt",
        content_type="text/plain",
    )

    with session_factory() as session:
        persisted = session.scalar(select(Statement).where(Statement.uuid == statement.uuid))

    assert persisted is not None
    assert persisted.status == StatementStatus.READY_FOR_PARSING
    assert persisted.detected_file_type == "unknown"
    assert persisted.parser_type == "unknown"


def test_processing_service_failure_transitions_for_missing_statement() -> None:
    service, _ = _build_processing_service()

    with pytest.raises(StatementNotFoundError):
        service.process_statement(
            statement_uuid="a5e63886-61f4-4ec8-8f36-4d52a1653a4d",
            original_filename="missing.csv",
            content_type="text/csv",
        )


def test_processing_service_sets_failed_status_on_runtime_exception(monkeypatch) -> None:
    service, session_factory = _build_processing_service()
    user = _create_user(session_factory)
    statement = _create_statement(session_factory, user_id=user.id, file_type="csv")

    def _boom(*, extension: str, content_type: str | None = None) -> str:
        raise RuntimeError("detector crashed")

    monkeypatch.setattr(
        "walletmind.services.statement_processing_service.detect_file_type",
        _boom,
    )

    with pytest.raises(RuntimeError):
        service.process_statement(
            statement_uuid=statement.uuid,
            original_filename="import.csv",
            content_type="text/csv",
        )

    with session_factory() as session:
        persisted = session.scalar(select(Statement).where(Statement.uuid == statement.uuid))

    assert persisted is not None
    assert persisted.status == StatementStatus.FAILED
    assert persisted.processing_completed_at is not None
    assert persisted.processing_error is not None
