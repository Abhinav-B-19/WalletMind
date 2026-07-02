"""Tests for the WalletMind database foundation."""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import inspect, select
from sqlalchemy.engine import Engine

from backend.app.database.init_db import init_database
from backend.app.database.session import create_database_engine, create_session_factory
from backend.app.models.user import User


def test_database_initialization_creates_user_table() -> None:
    """Database initialization creates the expected users and statements schema."""
    database_engine = create_database_engine("sqlite+pysqlite:///:memory:")

    init_database(database_engine)

    inspector = inspect(database_engine)
    user_columns = {column["name"] for column in inspector.get_columns("users")}
    user_indexes = {index["name"] for index in inspector.get_indexes("users")}
    statement_columns = {
        column["name"] for column in inspector.get_columns("statements")
    }
    statement_indexes = {
        index["name"] for index in inspector.get_indexes("statements")
    }

    assert "users" in inspector.get_table_names()
    assert "statements" in inspector.get_table_names()
    assert {
        "id",
        "uuid",
        "full_name",
        "occupation",
        "monthly_income",
        "currency",
        "financial_goal",
        "created_at",
        "updated_at",
    }.issubset(user_columns)
    assert "ix_users_uuid" in user_indexes
    assert "ix_users_currency" in user_indexes
    assert "ix_users_created_at" in user_indexes

    assert {
        "id",
        "uuid",
        "user_id",
        "original_filename",
        "stored_filename",
        "bank_name",
        "file_type",
        "file_size",
        "status",
        "uploaded_at",
        "updated_at",
    }.issubset(statement_columns)
    assert "ix_statements_uuid" in statement_indexes
    assert "ix_statements_user_id" in statement_indexes
    assert "ix_statements_status" in statement_indexes
    assert "ix_statements_uploaded_at" in statement_indexes
    assert "ix_statements_stored_filename" in statement_indexes
    assert "ix_statements_user_id_status" in statement_indexes
    assert "ix_statements_user_id_uploaded_at" in statement_indexes


def test_user_model_persists_with_generated_uuid_and_timestamps() -> None:
    """User records persist with generated UUIDs and database timestamps."""
    database_engine: Engine = create_database_engine("sqlite+pysqlite:///:memory:")
    session_factory = create_session_factory(database_engine)
    init_database(database_engine)

    with session_factory() as session:
        user = User(
            full_name="Ada Lovelace",
            occupation="Mathematician",
            monthly_income=Decimal("7500.00"),
            currency="USD",
            financial_goal="Build long-term financial resilience.",
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        persisted_user = session.scalar(select(User).where(User.uuid == user.uuid))

    assert persisted_user is not None
    assert UUID(persisted_user.uuid)
    assert persisted_user.full_name == "Ada Lovelace"
    assert persisted_user.created_at is not None
    assert persisted_user.updated_at is not None