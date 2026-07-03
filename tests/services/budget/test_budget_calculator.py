from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

from backend.app.services.budget.budget_calculator import BudgetCalculator
from backend.app.services.health.health_score_calculator import HealthScoreCalculator
from walletmind.schemas.transaction import TransactionDTO


def _tx(
    *,
    tx_date: date,
    amount: str,
    tx_type: str,
    category: str,
    merchant: str,
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


def _health(transactions: list[TransactionDTO]):
    return HealthScoreCalculator().calculate(
        statement_uuid=uuid4(),
        transactions=transactions,
    )


def test_budget_calculation_and_allocation() -> None:
    transactions = [
        _tx(
            tx_date=date(2026, 1, 1),
            amount="8000.00",
            tx_type="credit",
            category="Income",
            merchant="Employer",
        ),
        _tx(
            tx_date=date(2026, 1, 5),
            amount="-8500.00",
            tx_type="debit",
            category="Food",
            merchant="FoodCo",
        ),
        _tx(
            tx_date=date(2026, 1, 10),
            amount="-4000.00",
            tx_type="debit",
            category="Fuel",
            merchant="FuelCo",
        ),
        _tx(
            tx_date=date(2026, 1, 12),
            amount="-6000.00",
            tx_type="debit",
            category="Shopping",
            merchant="ShopCo",
        ),
    ]

    result = BudgetCalculator().calculate(
        statement_uuid=uuid4(),
        transactions=transactions,
        health=_health(transactions),
    )

    assert "Food" in result.monthly_budget
    assert (
        result.monthly_budget["Food"].recommended
        <= result.monthly_budget["Food"].historical
    )
    assert result.overall_potential_savings >= 0


def test_overspending_detection_and_potential_savings() -> None:
    transactions = [
        _tx(
            tx_date=date(2026, 1, 1),
            amount="10000.00",
            tx_type="credit",
            category="Income",
            merchant="Employer",
        ),
        _tx(
            tx_date=date(2026, 1, 3),
            amount="-4500.00",
            tx_type="debit",
            category="Shopping",
            merchant="ShopCo",
        ),
    ]

    result = BudgetCalculator().calculate(
        statement_uuid=uuid4(),
        transactions=transactions,
        health=_health(transactions),
    )

    assert "Shopping" in result.overspending_categories
    assert result.monthly_budget["Shopping"].potential_saving > 0
    assert (
        result.overall_potential_savings
        == result.monthly_budget["Shopping"].potential_saving
    )


def test_income_only_statement_budget() -> None:
    transactions = [
        _tx(
            tx_date=date(2026, 1, 1),
            amount="4000.00",
            tx_type="credit",
            category="Income",
            merchant="Employer",
        )
    ]

    result = BudgetCalculator().calculate(
        statement_uuid=uuid4(),
        transactions=transactions,
        health=_health(transactions),
    )

    assert result.monthly_budget == {}
    assert result.overall_potential_savings == 0
    assert result.discretionary_spending_allowance >= 0


def test_expense_only_statement_budget() -> None:
    transactions = [
        _tx(
            tx_date=date(2026, 1, 3),
            amount="-2500.00",
            tx_type="debit",
            category="Rent",
            merchant="Landlord",
            recurring=True,
        ),
        _tx(
            tx_date=date(2026, 1, 8),
            amount="-1000.00",
            tx_type="debit",
            category="Food",
            merchant="FoodCo",
        ),
    ]

    result = BudgetCalculator().calculate(
        statement_uuid=uuid4(),
        transactions=transactions,
        health=_health(transactions),
    )

    assert (
        result.monthly_budget["Rent"].recommended
        <= result.monthly_budget["Rent"].historical
    )
    assert result.discretionary_spending_allowance == 0


def test_large_statement_budget() -> None:
    transactions: list[TransactionDTO] = []
    for month in range(1, 13):
        transactions.append(
            _tx(
                tx_date=date(2026, month, 1),
                amount="7000.00",
                tx_type="credit",
                category="Income",
                merchant="Employer",
            )
        )
        transactions.append(
            _tx(
                tx_date=date(2026, month, 5),
                amount="-2500.00",
                tx_type="debit",
                category="Rent",
                merchant="Landlord",
                recurring=True,
            )
        )
        for day in range(6, 21):
            transactions.append(
                _tx(
                    tx_date=date(2026, month, min(day, 28)),
                    amount="-120.00",
                    tx_type="debit",
                    category="Food",
                    merchant=f"Food-{day}",
                )
            )

    result = BudgetCalculator().calculate(
        statement_uuid=uuid4(),
        transactions=transactions,
        health=_health(transactions),
    )

    assert len(result.monthly_budget) >= 2
    assert result.overall_potential_savings >= 0


def test_budget_excludes_income_categories_from_budget_outputs() -> None:
    transactions = [
        _tx(
            tx_date=date(2026, 1, 1),
            amount="12000.00",
            tx_type="credit",
            category="Income",
            merchant="Employer",
        ),
        _tx(
            tx_date=date(2026, 1, 3),
            amount="-12000.00",
            tx_type="debit",
            category="Salary",
            merchant="Payroll Adjustment",
        ),
        _tx(
            tx_date=date(2026, 1, 8),
            amount="-1800.00",
            tx_type="debit",
            category="Food",
            merchant="Grocer",
        ),
    ]

    result = BudgetCalculator().calculate(
        statement_uuid=uuid4(),
        transactions=transactions,
        health=_health(transactions),
    )

    assert "Salary" not in result.monthly_budget
    assert "Food" in result.monthly_budget
    assert "Salary" not in result.overspending_categories
    assert all(item["category"] != "Salary" for item in result.category_analysis)
