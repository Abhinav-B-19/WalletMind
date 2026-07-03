"""Tests for transaction persistence and duplicate prevention."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from backend.app.database.init_db import init_database
from backend.app.database.session import create_database_engine, create_session_factory
from backend.app.models.statement import Statement, StatementStatus
from backend.app.models.user import User
from walletmind.schemas.transaction import TransactionCreateDTO
from walletmind.services.transaction_service import TransactionService


def _setup() -> tuple[TransactionService, object, str]:
    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    session_factory = create_session_factory(engine)
    init_database(engine)

    with session_factory() as session:
        user = User(
            full_name="Alex Doe",
            occupation="Engineer",
            monthly_income=Decimal("1000.00"),
            currency="USD",
            financial_goal="Goal",
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        statement = Statement(
            user_id=user.id,
            original_filename="axis.csv",
            stored_filename="axis.csv",
            file_type="csv",
            file_size=123,
            status=StatementStatus.READY_FOR_PARSING,
        )
        session.add(statement)
        session.commit()
        session.refresh(statement)
        statement_uuid = statement.uuid

    return TransactionService(session_factory=session_factory), session_factory, statement_uuid


def test_duplicate_prevention() -> None:
    service, _, statement_uuid = _setup()

    tx = TransactionCreateDTO(
        transaction_date=date(2026, 1, 1),
        description="Salary",
        debit=None,
        credit=Decimal("1000.00"),
        amount=Decimal("1000.00"),
        transaction_type="credit",
        balance=Decimal("1000.00"),
        currency="INR",
        reference_number="-",
        raw_row_json={"r": 1},
    )

    inserted_1, duplicates_1 = service.store_transactions(
        statement_uuid=statement_uuid,
        transactions=[tx],
    )
    inserted_2, duplicates_2 = service.store_transactions(
        statement_uuid=statement_uuid,
        transactions=[tx],
    )

    assert inserted_1 == 1
    assert duplicates_1 == 0
    assert inserted_2 == 0
    assert duplicates_2 == 1
