"""Tests for statement persistence and validation behavior."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

import pytest
from pydantic import ValidationError
from sqlalchemy import select

from backend.app.database.init_db import init_database
from backend.app.database.session import create_database_engine, create_session_factory
from backend.app.models.statement import Statement, StatementStatus
from backend.app.models.user import User
from walletmind.schemas.statement import StatementCreate, StatementRead


def _create_user(session_factory) -> User:
    with session_factory() as session:
        user = User(
            full_name="Grace Hopper",
            occupation="Computer Scientist",
            monthly_income=Decimal("9000.00"),
            currency="USD",
            financial_goal="Build emergency fund.",
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


def test_statement_creation_persists_expected_fields() -> None:
    database_engine = create_database_engine("sqlite+pysqlite:///:memory:")
    session_factory = create_session_factory(database_engine)
    init_database(database_engine)
    user = _create_user(session_factory)

    with session_factory() as session:
        statement = Statement(
            user_id=user.id,
            original_filename="jan_statement.pdf",
            stored_filename="6a0b3c6e-jan.pdf",
            bank_name="Example Bank",
            file_type="application/pdf",
            file_size=248130,
            status=StatementStatus.UPLOADED,
        )
        session.add(statement)
        session.commit()
        session.refresh(statement)

        persisted = session.scalar(select(Statement).where(Statement.id == statement.id))

    assert persisted is not None
    assert persisted.user_id == user.id
    assert UUID(persisted.uuid)
    assert persisted.status == StatementStatus.UPLOADED
    assert persisted.uploaded_at is not None
    assert persisted.updated_at is not None


def test_statement_user_relationship_roundtrip() -> None:
    database_engine = create_database_engine("sqlite+pysqlite:///:memory:")
    session_factory = create_session_factory(database_engine)
    init_database(database_engine)
    user = _create_user(session_factory)

    with session_factory() as session:
        statement = Statement(
            user_id=user.id,
            original_filename="feb_statement.csv",
            stored_filename="7f8e9d0c-feb.csv",
            bank_name="Demo Credit Union",
            file_type="text/csv",
            file_size=1024,
        )
        session.add(statement)
        session.commit()
        session.refresh(statement)

        loaded_statement = session.scalar(select(Statement).where(Statement.id == statement.id))
        loaded_user = session.scalar(select(User).where(User.id == user.id))

    assert loaded_statement is not None
    assert loaded_user is not None
    assert loaded_statement.user is not None
    assert loaded_statement.user.id == loaded_user.id
    assert len(loaded_user.statements) == 1
    assert loaded_user.statements[0].id == loaded_statement.id


def test_statement_rows_are_deleted_when_user_is_deleted() -> None:
    database_engine = create_database_engine("sqlite+pysqlite:///:memory:")
    session_factory = create_session_factory(database_engine)
    init_database(database_engine)
    user = _create_user(session_factory)

    with session_factory() as session:
        statement = Statement(
            user_id=user.id,
            original_filename="mar_statement.pdf",
            stored_filename="1234-mar.pdf",
            bank_name="Bank Alpha",
            file_type="application/pdf",
            file_size=4096,
        )
        session.add(statement)
        session.commit()

        created_statement_id = statement.id

        persistent_user = session.scalar(select(User).where(User.id == user.id))
        assert persistent_user is not None
        session.delete(persistent_user)
        session.commit()

        remaining_statement = session.scalar(
            select(Statement).where(Statement.id == created_statement_id)
        )

    assert remaining_statement is None


def test_statement_schema_validation_enforces_constraints() -> None:
    valid = StatementCreate(
        user_id=1,
        original_filename="apr_statement.pdf",
        stored_filename="uuid-apr.pdf",
        bank_name="Bank Beta",
        file_type="application/pdf",
        file_size=2048,
    )
    assert valid.status == StatementStatus.UPLOADED

    with pytest.raises(ValidationError):
        StatementCreate(
            user_id=0,
            original_filename="apr_statement.pdf",
            stored_filename="uuid-apr.pdf",
            bank_name="Bank Beta",
            file_type="application/pdf",
            file_size=2048,
        )

    with pytest.raises(ValidationError):
        StatementCreate(
            user_id=1,
            original_filename="apr_statement.pdf",
            stored_filename="uuid-apr.pdf",
            bank_name="Bank Beta",
            file_type="application/pdf",
            file_size=0,
        )

    with pytest.raises(ValidationError):
        StatementCreate(
            user_id=1,
            original_filename="apr_statement.pdf",
            stored_filename="uuid-apr.pdf",
            bank_name="Bank Beta",
            file_type="application/pdf",
            file_size=2048,
            status="queued",
        )

    parsed = StatementRead.model_validate(
        {
            "id": 99,
            "uuid": "7fe95fdc-574c-4f8d-80df-8e6ddab9e98e",
            "user_id": 1,
            "original_filename": "apr_statement.pdf",
            "stored_filename": "uuid-apr.pdf",
            "bank_name": "Bank Beta",
            "file_type": "application/pdf",
            "file_size": 2048,
            "status": "uploaded",
            "uploaded_at": "2026-07-02T10:00:00Z",
            "updated_at": "2026-07-02T10:00:00Z",
        }
    )
    assert isinstance(parsed.uuid, UUID)
