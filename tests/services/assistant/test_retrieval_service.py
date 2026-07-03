from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

from backend.app.services.assistant.retrieval_service import RetrievalService
from walletmind.schemas.transaction import TransactionDTO


class StubTransactionService:
    def __init__(self, transactions: list[TransactionDTO]) -> None:
        self._transactions = transactions

    def get_statement_transactions(self, *, statement_uuid):
        return self._transactions


def _tx(
    *,
    description: str,
    amount: str,
    tx_type: str,
    month: int,
    merchant: str,
    category: str,
    channel: str,
    recurring: bool = False,
) -> TransactionDTO:
    value = Decimal(amount)
    return TransactionDTO(
        transaction_uuid=uuid4(),
        statement_uuid=uuid4(),
        transaction_date=date(2026, month, 5),
        description=description,
        debit=value if tx_type == "debit" else None,
        credit=value if tx_type == "credit" else None,
        amount=value,
        transaction_type=tx_type,
        balance=None,
        currency="USD",
        reference_number=None,
        merchant_name=merchant,
        bank_gateway=None,
        category=category,
        subcategory=None,
        payment_channel=channel,
        transaction_kind="income" if tx_type == "credit" else "expense",
        confidence_score=85,
        raw_description=description,
        clean_description=description.lower(),
        normalized_transaction_type="income" if tx_type == "credit" else "expense",
        flags={"is_recurring": recurring},
        raw_row_json={},
        created_at=datetime.now(UTC),
    )


def test_retrieve_filters_by_merchant() -> None:
    statement_uuid = uuid4()
    service = RetrievalService(
        transaction_service=StubTransactionService(
            [
                _tx(
                    description="Coffee purchase",
                    amount="-5.50",
                    tx_type="debit",
                    month=1,
                    merchant="Starbucks",
                    category="Food & Dining",
                    channel="Card",
                ),
                _tx(
                    description="Fuel",
                    amount="-40.00",
                    tx_type="debit",
                    month=1,
                    merchant="Shell",
                    category="Fuel",
                    channel="Card",
                ),
            ]
        )
    )

    result = service.retrieve(
        statement_uuid=statement_uuid,
        question="How much did I spend at Starbucks?",
    )

    assert len(result.transactions) == 1
    assert result.transactions[0].merchant_name == "Starbucks"


def test_retrieve_filters_by_category_month_and_amount() -> None:
    service = RetrievalService(
        transaction_service=StubTransactionService(
            [
                _tx(
                    description="Groceries",
                    amount="-120.00",
                    tx_type="debit",
                    month=2,
                    merchant="Whole Foods",
                    category="Food & Dining",
                    channel="UPI",
                ),
                _tx(
                    description="Lunch",
                    amount="-18.00",
                    tx_type="debit",
                    month=2,
                    merchant="Cafe",
                    category="Food & Dining",
                    channel="UPI",
                ),
                _tx(
                    description="Food",
                    amount="-90.00",
                    tx_type="debit",
                    month=1,
                    merchant="Trader Joe's",
                    category="Food & Dining",
                    channel="UPI",
                ),
            ]
        )
    )

    result = service.retrieve(
        statement_uuid=uuid4(),
        question="Show food spending in February above 100",
    )

    assert len(result.transactions) == 1
    assert result.transactions[0].description == "Groceries"


def test_retrieve_filters_recurring_subscriptions() -> None:
    service = RetrievalService(
        transaction_service=StubTransactionService(
            [
                _tx(
                    description="Netflix",
                    amount="-14.99",
                    tx_type="debit",
                    month=3,
                    merchant="Netflix",
                    category="Entertainment",
                    channel="Card",
                    recurring=True,
                ),
                _tx(
                    description="Movie",
                    amount="-22.00",
                    tx_type="debit",
                    month=3,
                    merchant="AMC",
                    category="Entertainment",
                    channel="Card",
                    recurring=False,
                ),
            ]
        )
    )

    result = service.retrieve(
        statement_uuid=uuid4(),
        question="List recurring subscriptions",
    )

    assert len(result.transactions) == 1
    assert result.transactions[0].merchant_name == "Netflix"
