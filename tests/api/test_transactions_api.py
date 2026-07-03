from __future__ import annotations

from datetime import date
from decimal import Decimal
import json

from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.app.database.init_db import init_database
from backend.app.database.session import create_database_engine, create_session_factory
from backend.app.main import create_app
from backend.app.models.statement import Statement, StatementStatus
from backend.app.models.transaction import Transaction
from backend.app.models.user import User
from walletmind.services.processing_dispatcher import ProcessingDispatcher
from walletmind.services.statement_processing_service import StatementProcessingService
from walletmind.services.statement_upload_service import StatementUploadService
from walletmind.services.transaction_service import TransactionService
from walletmind.services.user_service import UserService


def _setup_client(tmp_path):
    database_url = f"sqlite+pysqlite:///{(tmp_path / 'tx-api-test.db').as_posix()}"
    database_engine = create_database_engine(database_url)
    session_factory = create_session_factory(database_engine)
    init_database(database_engine)

    app = create_app()
    app.state.user_service = UserService(session_factory=session_factory)
    app.state.statement_upload_service = StatementUploadService(
        session_factory=session_factory,
        upload_dir=tmp_path / "uploads",
    )
    app.state.statement_processing_service = StatementProcessingService(
        session_factory=session_factory,
    )
    app.state.transaction_service = TransactionService(session_factory=session_factory)
    app.state.processing_dispatcher = ProcessingDispatcher(
        processing_service=app.state.statement_processing_service,
    )

    return TestClient(app), session_factory


def _create_seed_data(session_factory) -> tuple[str, str]:
    with session_factory() as session:
        user = User(
            full_name="Riley Hart",
            occupation="Engineer",
            monthly_income=Decimal("7300.00"),
            currency="USD",
            financial_goal="Save more.",
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        statement = Statement(
            user_id=user.id,
            original_filename="seed.csv",
            stored_filename="seed.csv",
            file_type="csv",
            file_size=120,
            status=StatementStatus.READY_FOR_ANALYSIS,
            parser_type="generic_csv_parser",
            bank_name="Unknown",
        )
        session.add(statement)
        session.commit()
        session.refresh(statement)

        session.add_all(
            [
                Transaction(
                    statement_id=statement.id,
                    transaction_date=date(2026, 1, 1),
                    description="Salary",
                    debit=None,
                    credit=Decimal("2000.00"),
                    amount=Decimal("2000.00"),
                    transaction_type="credit",
                    balance=Decimal("3000.00"),
                    currency="USD",
                    reference_number="A1",
                    merchant_name="Employer Payroll",
                    bank_gateway=None,
                    category="Income",
                    raw_description="Salary",
                    clean_description="salary",
                    normalized_transaction_type="income",
                    is_internal_transfer=False,
                    is_income=True,
                    is_expense=False,
                    raw_row_json=json.dumps({"row": 1}),
                ),
                Transaction(
                    statement_id=statement.id,
                    transaction_date=date(2026, 1, 2),
                    description="Groceries",
                    debit=Decimal("-120.00"),
                    credit=None,
                    amount=Decimal("-120.00"),
                    transaction_type="debit",
                    balance=Decimal("2880.00"),
                    currency="USD",
                    reference_number="A2",
                    merchant_name="Local Store",
                    bank_gateway=None,
                    category="Food & Dining",
                    raw_description="Groceries",
                    clean_description="groceries",
                    normalized_transaction_type="expense",
                    is_internal_transfer=False,
                    is_income=False,
                    is_expense=True,
                    raw_row_json=json.dumps({"row": 2}),
                ),
            ]
        )
        session.commit()

        return statement.uuid, user.uuid


def test_get_statement_transactions(tmp_path) -> None:
    client, session_factory = _setup_client(tmp_path)
    statement_uuid, _ = _create_seed_data(session_factory)

    response = client.get(f"/api/v1/statements/{statement_uuid}/transactions")
    assert response.status_code == 200

    payload = response.json()
    assert payload["success"] is True
    assert len(payload["data"]) == 2
    assert payload["data"][0]["statement_uuid"] == statement_uuid
    assert payload["data"][0]["category"]
    assert "clean_description" in payload["data"][0]
    assert "bank_gateway" in payload["data"][0]
    assert "normalized_transaction_type" in payload["data"][0]
    assert "flags" in payload["data"][0]


def test_list_transactions_with_filters(tmp_path) -> None:
    client, session_factory = _setup_client(tmp_path)
    statement_uuid, _ = _create_seed_data(session_factory)

    response = client.get(
        "/api/v1/transactions",
        params={
            "statement_uuid": statement_uuid,
            "from_date": "2026-01-02",
            "to_date": "2026-01-02",
            "min_amount": "-500",
            "max_amount": "0",
            "page": 1,
            "page_size": 10,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert len(payload["data"]) == 1
    assert payload["data"][0]["description"] == "Groceries"


def test_list_transactions_with_search_and_category_filter(tmp_path) -> None:
    client, session_factory = _setup_client(tmp_path)
    statement_uuid, _ = _create_seed_data(session_factory)

    response = client.get(
        "/api/v1/transactions",
        params={
            "statement_uuid": statement_uuid,
            "q": "payroll",
            "category": "Income",
            "normalized_type": "income",
            "page": 1,
            "page_size": 10,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert len(payload["data"]) == 1
    assert payload["data"][0]["category"] == "Income"
