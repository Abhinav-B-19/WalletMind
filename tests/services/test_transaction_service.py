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


def test_store_transactions_persists_enriched_fields() -> None:
    service, _, statement_uuid = _setup()

    tx = TransactionCreateDTO(
        transaction_date=date(2026, 1, 2),
        description="UPI/P2M/GROWW SIP",
        debit=Decimal("-500.00"),
        credit=None,
        amount=Decimal("-500.00"),
        transaction_type="debit",
        balance=Decimal("500.00"),
        currency="INR",
        reference_number="-",
        raw_row_json={"r": 2},
    )

    inserted, duplicates = service.store_transactions(
        statement_uuid=statement_uuid,
        transactions=[tx],
    )

    assert inserted == 1
    assert duplicates == 0

    rows = service.get_statement_transactions(statement_uuid=statement_uuid)
    assert rows
    assert rows[0].category == "Investment"
    assert rows[0].clean_description == "Groww Sip"
    assert rows[0].bank_gateway is None
    assert rows[0].payment_channel == "UPI"
    assert rows[0].confidence_score >= 0
    assert rows[0].normalized_transaction_type == "expense"


def test_list_transactions_supports_search_and_filters() -> None:
    service, _, statement_uuid = _setup()

    transactions = [
        TransactionCreateDTO(
            transaction_date=date(2026, 1, 3),
            description="UPI/P2M/BP Petrol Pump",
            debit=Decimal("-1000.00"),
            credit=None,
            amount=Decimal("-1000.00"),
            transaction_type="debit",
            balance=Decimal("1000.00"),
            currency="INR",
            reference_number="-",
            raw_row_json={"r": 3},
        ),
        TransactionCreateDTO(
            transaction_date=date(2026, 1, 4),
            description="UPI/P2M/JioHotstar",
            debit=Decimal("-299.00"),
            credit=None,
            amount=Decimal("-299.00"),
            transaction_type="debit",
            balance=Decimal("701.00"),
            currency="INR",
            reference_number="-",
            raw_row_json={"r": 4},
        ),
    ]
    service.store_transactions(statement_uuid=statement_uuid, transactions=transactions)

    fuel_only = service.list_transactions(
        statement_uuid=statement_uuid,
        category="Fuel",
        page=1,
        page_size=20,
    )
    assert len(fuel_only) == 1
    assert fuel_only[0].category == "Fuel"

    entertainment_only = service.list_transactions(
        statement_uuid=statement_uuid,
        normalized_type="expense",
        q="hotstar",
        page=1,
        page_size=20,
    )
    assert len(entertainment_only) == 1
    assert entertainment_only[0].category == "Entertainment"


def test_reprocessing_does_not_duplicate_enrichment() -> None:
    service, _, statement_uuid = _setup()

    tx = TransactionCreateDTO(
        transaction_date=date(2026, 1, 5),
        description="UPI/P2M/NETFLIX",
        debit=Decimal("-199.00"),
        credit=None,
        amount=Decimal("-199.00"),
        transaction_type="debit",
        balance=Decimal("500.00"),
        currency="INR",
        reference_number="-",
        raw_row_json={"r": 5},
    )

    first_inserted, _ = service.store_transactions(
        statement_uuid=statement_uuid,
        transactions=[tx],
    )
    second_inserted, second_duplicates = service.store_transactions(
        statement_uuid=statement_uuid,
        transactions=[tx],
    )

    assert first_inserted == 1
    assert second_inserted == 0
    assert second_duplicates == 1
