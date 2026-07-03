from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

from backend.app.services.budget.recommendation_prioritizer import (
    RecommendationPrioritizer,
)
from backend.app.services.health.health_score_calculator import HealthScoreCalculator
from walletmind.schemas.transaction import TransactionDTO


def _tx(*, amount: str, tx_type: str, tx_date: date, category: str) -> TransactionDTO:
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
        merchant_name="M",
        bank_gateway=None,
        category=category,
        subcategory=None,
        payment_channel="Card",
        transaction_kind="income" if tx_type == "credit" else "expense",
        confidence_score=90,
        raw_description="raw",
        clean_description="clean",
        normalized_transaction_type="income" if tx_type == "credit" else "expense",
        flags={"is_income": tx_type == "credit", "is_expense": tx_type == "debit"},
        raw_row_json={},
        created_at=datetime.now(UTC),
    )


def test_recommendation_prioritization_orders_by_impact() -> None:
    health = HealthScoreCalculator().calculate(
        statement_uuid=uuid4(),
        transactions=[
            _tx(
                amount="4000.00",
                tx_type="credit",
                tx_date=date(2026, 1, 1),
                category="Income",
            ),
            _tx(
                amount="-1800.00",
                tx_type="debit",
                tx_date=date(2026, 1, 2),
                category="Shopping",
            ),
        ],
    )

    categories = [
        {
            "category": "Shopping",
            "historical": 1800.0,
            "recommended": 1200.0,
            "potential_saving": 600.0,
            "utilization_ratio": 1.5,
        },
        {
            "category": "Food",
            "historical": 2500.0,
            "recommended": 1100.0,
            "potential_saving": 1400.0,
            "utilization_ratio": 2.2,
        },
    ]

    prioritized = RecommendationPrioritizer().prioritize(
        categories=categories,
        health=health,
    )

    assert len(prioritized) == 2
    assert prioritized[0].category == "Food"
    assert (
        prioritized[0].estimated_monthly_saving
        >= prioritized[1].estimated_monthly_saving
    )
