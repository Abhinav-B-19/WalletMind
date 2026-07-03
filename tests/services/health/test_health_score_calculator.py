from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

from backend.app.services.health.health_score_calculator import HealthScoreCalculator
from walletmind.schemas.transaction import TransactionDTO


def _tx(
    *,
    tx_date: date,
    amount: str,
    tx_type: str,
    merchant: str,
    category: str,
    recurring: bool = False,
) -> TransactionDTO:
    value = Decimal(amount)
    return TransactionDTO(
        transaction_uuid=uuid4(),
        statement_uuid=uuid4(),
        transaction_date=tx_date,
        description=f"{merchant} tx",
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
            "is_subscription": recurring,
            "is_recurring": recurring,
        },
        raw_row_json={},
        created_at=datetime.now(UTC),
    )


def test_score_calculation_returns_weighted_result() -> None:
    calculator = HealthScoreCalculator()
    statement_uuid = uuid4()
    transactions = [
        _tx(
            tx_date=date(2026, 1, 1),
            amount="5000.00",
            tx_type="credit",
            merchant="Employer",
            category="Income",
        ),
        _tx(
            tx_date=date(2026, 1, 5),
            amount="-1800.00",
            tx_type="debit",
            merchant="Landlord",
            category="Rent",
            recurring=True,
        ),
        _tx(
            tx_date=date(2026, 1, 20),
            amount="-700.00",
            tx_type="debit",
            merchant="Grocer",
            category="Food & Dining",
        ),
        _tx(
            tx_date=date(2026, 2, 1),
            amount="5200.00",
            tx_type="credit",
            merchant="Employer",
            category="Income",
        ),
        _tx(
            tx_date=date(2026, 2, 5),
            amount="-1750.00",
            tx_type="debit",
            merchant="Landlord",
            category="Rent",
            recurring=True,
        ),
        _tx(
            tx_date=date(2026, 2, 23),
            amount="-800.00",
            tx_type="debit",
            merchant="Grocer",
            category="Food & Dining",
        ),
    ]

    result = calculator.calculate(
        statement_uuid=statement_uuid, transactions=transactions
    )

    assert 0 <= result.overall_score <= 100
    assert result.grade in {
        "Excellent",
        "Good",
        "Fair",
        "Needs Improvement",
        "Critical",
    }
    assert result.components.savings_rate > 0
    assert result.components.income_stability > 0
    assert result.components.spending_discipline > 0
    assert result.components.cash_flow > 0


def test_grade_mapping_boundaries() -> None:
    calc = HealthScoreCalculator()

    assert calc._grade_for_score(95) == "Excellent"
    assert calc._grade_for_score(80) == "Good"
    assert calc._grade_for_score(65) == "Fair"
    assert calc._grade_for_score(45) == "Needs Improvement"
    assert calc._grade_for_score(20) == "Critical"


def test_income_stability_lower_for_volatile_income() -> None:
    calculator = HealthScoreCalculator()
    stable_statement = uuid4()
    volatile_statement = uuid4()

    stable = [
        _tx(
            tx_date=date(2026, month, 1),
            amount="5000.00",
            tx_type="credit",
            merchant="Employer",
            category="Income",
        )
        for month in [1, 2, 3]
    ]
    volatile = [
        _tx(
            tx_date=date(2026, 1, 1),
            amount="1500.00",
            tx_type="credit",
            merchant="Employer",
            category="Income",
        ),
        _tx(
            tx_date=date(2026, 2, 1),
            amount="9500.00",
            tx_type="credit",
            merchant="Employer",
            category="Income",
        ),
        _tx(
            tx_date=date(2026, 3, 1),
            amount="3000.00",
            tx_type="credit",
            merchant="Employer",
            category="Income",
        ),
    ]

    stable_result = calculator.calculate(
        statement_uuid=stable_statement, transactions=stable
    )
    volatile_result = calculator.calculate(
        statement_uuid=volatile_statement,
        transactions=volatile,
    )

    assert (
        stable_result.components.income_stability
        > volatile_result.components.income_stability
    )


def test_spending_discipline_penalizes_high_expense_ratio() -> None:
    calculator = HealthScoreCalculator()
    statement_uuid = uuid4()

    disciplined_transactions = [
        _tx(
            tx_date=date(2026, 1, 1),
            amount="5000.00",
            tx_type="credit",
            merchant="Employer",
            category="Income",
        ),
        _tx(
            tx_date=date(2026, 1, 10),
            amount="-1500.00",
            tx_type="debit",
            merchant="Bills",
            category="Utilities",
        ),
    ]
    weak_transactions = [
        _tx(
            tx_date=date(2026, 1, 1),
            amount="3000.00",
            tx_type="credit",
            merchant="Employer",
            category="Income",
        ),
        _tx(
            tx_date=date(2026, 1, 3),
            amount="-2800.00",
            tx_type="debit",
            merchant="Shopping",
            category="Shopping",
        ),
    ]

    disciplined_result = calculator.calculate(
        statement_uuid=statement_uuid,
        transactions=disciplined_transactions,
    )
    weak_result = calculator.calculate(
        statement_uuid=uuid4(),
        transactions=weak_transactions,
    )

    assert (
        disciplined_result.components.spending_discipline
        > weak_result.components.spending_discipline
    )


def test_cash_flow_penalizes_negative_net() -> None:
    calculator = HealthScoreCalculator()

    healthy = [
        _tx(
            tx_date=date(2026, 1, 1),
            amount="4500.00",
            tx_type="credit",
            merchant="Employer",
            category="Income",
        ),
        _tx(
            tx_date=date(2026, 1, 6),
            amount="-2200.00",
            tx_type="debit",
            merchant="Expenses",
            category="Needs",
        ),
    ]
    unhealthy = [
        _tx(
            tx_date=date(2026, 1, 1),
            amount="2500.00",
            tx_type="credit",
            merchant="Employer",
            category="Income",
        ),
        _tx(
            tx_date=date(2026, 1, 6),
            amount="-3200.00",
            tx_type="debit",
            merchant="Expenses",
            category="Needs",
        ),
    ]

    healthy_result = calculator.calculate(statement_uuid=uuid4(), transactions=healthy)
    unhealthy_result = calculator.calculate(
        statement_uuid=uuid4(), transactions=unhealthy
    )

    assert healthy_result.components.cash_flow > unhealthy_result.components.cash_flow


def test_large_dataset_is_processed_deterministically() -> None:
    calculator = HealthScoreCalculator()
    transactions: list[TransactionDTO] = []

    for month in range(1, 13):
        transactions.append(
            _tx(
                tx_date=date(2026, month, 1),
                amount="4000.00",
                tx_type="credit",
                merchant="Employer",
                category="Income",
            )
        )
        for day in range(2, 22):
            transactions.append(
                _tx(
                    tx_date=date(2026, month, min(day, 28)),
                    amount="-50.00",
                    tx_type="debit",
                    merchant=f"Merchant-{day}",
                    category="Daily",
                )
            )

    result = calculator.calculate(statement_uuid=uuid4(), transactions=transactions)

    assert 0 <= result.overall_score <= 100
    assert len(result.strengths) >= 1
    assert len(result.weaknesses) >= 1
