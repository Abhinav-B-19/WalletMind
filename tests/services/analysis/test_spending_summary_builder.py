from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

from backend.app.services.analysis.spending_summary_builder import (
    SpendingSummaryBuilder,
)
from walletmind.schemas.transaction import TransactionDTO


def _tx(
    *,
    amount: str,
    transaction_type: str,
    category: str,
    merchant: str,
    tx_date: date,
    is_income: bool,
    is_expense: bool,
    is_subscription: bool = False,
) -> TransactionDTO:
    return TransactionDTO(
        transaction_uuid=uuid4(),
        statement_uuid=uuid4(),
        transaction_date=tx_date,
        description=f"{merchant} transaction",
        debit=Decimal(amount) if transaction_type == "debit" else None,
        credit=Decimal(amount) if transaction_type == "credit" else None,
        amount=Decimal(amount),
        transaction_type=transaction_type,
        balance=None,
        currency="USD",
        reference_number=None,
        merchant_name=merchant,
        bank_gateway=None,
        category=category,
        subcategory=None,
        payment_channel="Card",
        transaction_kind="income" if is_income else "expense",
        confidence_score=90,
        raw_description="redacted",
        clean_description="redacted",
        normalized_transaction_type="income" if is_income else "expense",
        flags={
            "is_income": is_income,
            "is_expense": is_expense,
            "is_subscription": is_subscription,
        },
        raw_row_json={},
        created_at=datetime.now(UTC),
    )



def test_summary_builder_computes_required_metrics() -> None:
    statement_uuid = uuid4()
    transactions = [
        _tx(
            amount="3000.00",
            transaction_type="credit",
            category="Income",
            merchant="Employer",
            tx_date=date(2026, 1, 1),
            is_income=True,
            is_expense=False,
        ),
        _tx(
            amount="-1200.00",
            transaction_type="debit",
            category="Rent",
            merchant="Landlord",
            tx_date=date(2026, 1, 2),
            is_income=False,
            is_expense=True,
        ),
        _tx(
            amount="-200.00",
            transaction_type="debit",
            category="Food",
            merchant="Grocer",
            tx_date=date(2026, 1, 5),
            is_income=False,
            is_expense=True,
            is_subscription=True,
        ),
        _tx(
            amount="1500.00",
            transaction_type="credit",
            category="Income",
            merchant="Freelance",
            tx_date=date(2026, 2, 1),
            is_income=True,
            is_expense=False,
        ),
    ]

    summary = SpendingSummaryBuilder().build(
        statement_uuid=statement_uuid,
        transactions=transactions,
    )

    assert summary.statement_uuid == statement_uuid
    assert summary.total_income == Decimal("4500.00")
    assert summary.total_expenses == Decimal("1400.00")
    assert summary.net_cash_flow == Decimal("3100.00")
    assert summary.savings_rate == 68.89
    assert summary.transaction_count == 4
    assert summary.credit_count == 2
    assert summary.debit_count == 2
    assert summary.category_totals["Rent"] == Decimal("1200.00")
    assert summary.category_totals["Food"] == Decimal("200.00")
    assert summary.top_spending_categories[0]["category"] == "Rent"
    assert summary.top_merchants[0]["merchant"] == "Landlord"
    assert summary.largest_expense is not None
    assert summary.largest_expense["merchant"] == "Landlord"
    assert summary.largest_income is not None
    assert summary.largest_income["merchant"] == "Employer"
    assert len(summary.monthly_trend) == 2
    assert summary.monthly_averages["income"] == 2250.0



def test_summary_payload_is_json_serializable() -> None:
    statement_uuid = uuid4()
    transactions = [
        _tx(
            amount="100.00",
            transaction_type="credit",
            category="Income",
            merchant="Employer",
            tx_date=date(2026, 1, 1),
            is_income=True,
            is_expense=False,
        )
    ]

    summary = SpendingSummaryBuilder().build(
        statement_uuid=statement_uuid,
        transactions=transactions,
    )

    payload = summary.as_prompt_payload()

    assert payload["statement_uuid"] == str(statement_uuid)
    assert payload["cash_flow"]["total_income"] == 100.0
    assert payload["cash_flow"]["total_expenses"] == 0.0
