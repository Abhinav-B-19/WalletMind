from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

from backend.app.services.report.report_builder import ReportBuilder
from walletmind.schemas.transaction import TransactionDTO


def _tx(
    *,
    tx_date: date,
    amount: str,
    tx_type: str,
    category: str,
    merchant: str,
    subscription: bool = False,
) -> TransactionDTO:
    value = Decimal(amount)
    return TransactionDTO(
        transaction_uuid=uuid4(),
        statement_uuid=uuid4(),
        transaction_date=tx_date,
        description="tx",
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
        payment_channel="Card",
        transaction_kind="income" if tx_type == "credit" else "expense",
        confidence_score=90,
        raw_description="raw",
        clean_description="clean",
        normalized_transaction_type="income" if tx_type == "credit" else "expense",
        flags={
            "is_income": tx_type == "credit",
            "is_expense": tx_type == "debit",
            "is_subscription": subscription,
            "is_recurring": subscription,
        },
        raw_row_json={},
        created_at=datetime.now(UTC),
    )


def test_report_builder_generates_deterministic_sections() -> None:
    transactions = [
        _tx(
            tx_date=date(2026, 1, 1),
            amount="6000.00",
            tx_type="credit",
            category="Income",
            merchant="Employer",
        ),
        _tx(
            tx_date=date(2026, 1, 5),
            amount="-2400.00",
            tx_type="debit",
            category="Rent",
            merchant="Landlord",
            subscription=True,
        ),
        _tx(
            tx_date=date(2026, 1, 10),
            amount="-1000.00",
            tx_type="debit",
            category="Food",
            merchant="Market",
        ),
    ]

    result = ReportBuilder().build(statement_uuid=uuid4(), transactions=transactions)

    sections = result.sections
    assert sections.health_score["overall_score"] >= 0
    assert (
        sections.financial_health["overall_score"]
        == sections.health_score["overall_score"]
    )
    assert sections.income_summary["total_income"] == 6000.0
    assert sections.expense_summary["total_expenses"] == 3400.0
    assert sections.cash_flow["net_cash_flow"] == 2600.0
    assert sections.spending_insights["subscriptions"]
    assert "overall_potential_savings" in sections.budget_recommendations
