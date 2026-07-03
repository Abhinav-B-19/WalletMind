from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

from backend.app.services.assistant.context_builder import ContextBuilder
from backend.app.services.assistant.retrieval_service import RetrievalResult
from walletmind.schemas.transaction import TransactionDTO


def _tx(*, amount: str, merchant: str) -> TransactionDTO:
    value = Decimal(amount)
    return TransactionDTO(
        transaction_uuid=uuid4(),
        statement_uuid=uuid4(),
        transaction_date=date(2026, 1, 7),
        description="test",
        debit=value,
        credit=None,
        amount=value,
        transaction_type="debit",
        balance=None,
        currency="USD",
        reference_number=None,
        merchant_name=merchant,
        bank_gateway=None,
        category="Food & Dining",
        subcategory=None,
        payment_channel="Card",
        transaction_kind="expense",
        confidence_score=90,
        raw_description="raw",
        clean_description="clean",
        normalized_transaction_type="expense",
        flags={"is_recurring": False},
        raw_row_json={},
        created_at=datetime.now(UTC),
    )


def test_build_context_with_summary_and_snippets() -> None:
    retrieval = RetrievalResult(
        statement_uuid=uuid4(),
        question="How much did I spend on food?",
        filters_applied={"category": "Food & Dining"},
        transactions=[
            _tx(amount="-20.00", merchant="A"),
            _tx(amount="-30.00", merchant="B"),
        ],
    )

    context = ContextBuilder().build(retrieval)

    assert context.summary["transaction_count"] == 2
    assert context.summary["total_amount"] == 50.0
    assert context.summary["average_amount"] == 25.0
    assert len(context.transactions) == 2
    assert context.transactions[0]["transaction_id"]
