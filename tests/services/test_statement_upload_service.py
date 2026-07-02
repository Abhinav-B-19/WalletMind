"""Unit tests for statement upload business logic."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

import pytest
from sqlalchemy import select

from backend.app.database.init_db import init_database
from backend.app.database.session import create_database_engine, create_session_factory
from backend.app.models.statement import Statement
from backend.app.models.user import User
from walletmind.exceptions import EmptyFileError, FileTooLargeError, UnsupportedFileTypeError
from walletmind.services.statement_upload_service import StatementUploadService


def _create_user(session_factory) -> User:
    with session_factory() as session:
        user = User(
            full_name="Taylor Swift",
            occupation="Analyst",
            monthly_income=Decimal("4200.00"),
            currency="USD",
            financial_goal="Track monthly spending.",
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


def _build_service(tmp_path, max_file_size_bytes: int = 10 * 1024 * 1024):
    database_engine = create_database_engine("sqlite+pysqlite:///:memory:")
    session_factory = create_session_factory(database_engine)
    init_database(database_engine)
    service = StatementUploadService(
        session_factory=session_factory,
        upload_dir=tmp_path / "uploads",
        max_file_size_bytes=max_file_size_bytes,
    )
    return service, session_factory


def test_upload_valid_csv(tmp_path) -> None:
    service, session_factory = _build_service(tmp_path)
    user = _create_user(session_factory)

    response = service.upload_statement(
        user_uuid=user.uuid,
        original_filename="statement.csv",
        file_bytes=b"date,amount\n2026-07-01,100\n",
    )

    assert response.original_filename == "statement.csv"
    assert response.file_type == "csv"
    assert response.file_size > 0
    assert response.stored_file_path is not None
    assert (tmp_path / "uploads" / response.stored_filename).exists()


def test_upload_valid_xlsx(tmp_path) -> None:
    service, session_factory = _build_service(tmp_path)
    user = _create_user(session_factory)

    response = service.upload_statement(
        user_uuid=user.uuid,
        original_filename="statement.xlsx",
        file_bytes=b"PK\x03\x04dummy-xlsx-content",
    )

    assert response.original_filename == "statement.xlsx"
    assert response.file_type == "xlsx"


def test_upload_valid_xls(tmp_path) -> None:
    service, session_factory = _build_service(tmp_path)
    user = _create_user(session_factory)

    response = service.upload_statement(
        user_uuid=user.uuid,
        original_filename="statement.xls",
        file_bytes=b"D0CF11E0A1B11AE1",
    )

    assert response.original_filename == "statement.xls"
    assert response.file_type == "xls"


def test_upload_valid_pdf(tmp_path) -> None:
    service, session_factory = _build_service(tmp_path)
    user = _create_user(session_factory)

    response = service.upload_statement(
        user_uuid=user.uuid,
        original_filename="statement.pdf",
        file_bytes=b"%PDF-1.7 sample",
    )

    assert response.original_filename == "statement.pdf"
    assert response.file_type == "pdf"
    assert response.parser_type == "pdf"


def test_upload_rejects_invalid_extension(tmp_path) -> None:
    service, session_factory = _build_service(tmp_path)
    user = _create_user(session_factory)

    with pytest.raises(UnsupportedFileTypeError):
        service.upload_statement(
            user_uuid=user.uuid,
            original_filename="statement.txt",
            file_bytes=b"not-supported",
        )


def test_upload_rejects_empty_file(tmp_path) -> None:
    service, session_factory = _build_service(tmp_path)
    user = _create_user(session_factory)

    with pytest.raises(EmptyFileError):
        service.upload_statement(
            user_uuid=user.uuid,
            original_filename="statement.csv",
            file_bytes=b"",
        )


def test_upload_rejects_oversized_file(tmp_path) -> None:
    service, session_factory = _build_service(tmp_path, max_file_size_bytes=4)
    user = _create_user(session_factory)

    with pytest.raises(FileTooLargeError):
        service.upload_statement(
            user_uuid=user.uuid,
            original_filename="statement.csv",
            file_bytes=b"12345",
        )


def test_upload_generates_uuid_stored_filename_and_persists_metadata(tmp_path) -> None:
    service, session_factory = _build_service(tmp_path)
    user = _create_user(session_factory)

    response = service.upload_statement(
        user_uuid=user.uuid,
        original_filename="statement.xls",
        file_bytes=b"D0CF11E0A1B11AE1",
    )

    parsed_uuid = UUID(response.stored_filename.removesuffix(".xls"))
    assert str(parsed_uuid)
    assert response.stored_filename.endswith(".xls")

    with session_factory() as session:
        statement = session.scalar(
            select(Statement).where(Statement.uuid == str(response.statement_uuid))
        )

    assert statement is not None
    assert statement.user_id == user.id
    assert statement.original_filename == "statement.xls"


def test_upload_assigns_parser_type_for_csv_and_excel(tmp_path) -> None:
    service, session_factory = _build_service(tmp_path)
    user = _create_user(session_factory)

    csv_response = service.upload_statement(
        user_uuid=user.uuid,
        original_filename="transactions.csv",
        file_bytes=b"date,amount\n2026-07-01,100\n",
    )
    xlsx_response = service.upload_statement(
        user_uuid=user.uuid,
        original_filename="transactions.xlsx",
        file_bytes=b"PK\x03\x04dummy-xlsx-content",
    )

    assert csv_response.parser_type == "csv"
    assert xlsx_response.parser_type == "excel"


def test_upload_assigns_analysis_status_queued(tmp_path) -> None:
    service, session_factory = _build_service(tmp_path)
    user = _create_user(session_factory)

    response = service.upload_statement(
        user_uuid=user.uuid,
        original_filename="status_check.csv",
        file_bytes=b"date,amount\n2026-07-01,100\n",
    )

    assert response.status == "queued"
    assert response.analysis_status == "queued"


def test_upload_sanitizes_original_filename(tmp_path) -> None:
    service, session_factory = _build_service(tmp_path)
    user = _create_user(session_factory)

    response = service.upload_statement(
        user_uuid=user.uuid,
        original_filename="../../bad name(1).csv",
        file_bytes=b"date,amount\n2026-07-01,100\n",
    )

    assert response.original_filename == "bad_name_1_.csv"

    with session_factory() as session:
        statement = session.scalar(
            select(Statement).where(Statement.uuid == str(response.statement_uuid))
        )

    assert statement is not None
    assert statement.original_filename == "bad_name_1_.csv"


def test_upload_persists_statement_with_queued_status(tmp_path) -> None:
    service, session_factory = _build_service(tmp_path)
    user = _create_user(session_factory)

    response = service.upload_statement(
        user_uuid=user.uuid,
        original_filename="queued_check.csv",
        file_bytes=b"date,amount\n2026-07-01,100\n",
    )

    with session_factory() as session:
        statement = session.scalar(
            select(Statement).where(Statement.uuid == str(response.statement_uuid))
        )

    assert statement is not None
    assert statement.status.value == "queued"
