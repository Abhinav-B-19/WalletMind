from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from backend.app.services.ai.exceptions import AIServiceError
from backend.app.services.report.executive_summary_builder import ExecutiveSummaryResult
from backend.app.services.report.financial_report_service import FinancialReportService
from backend.app.services.report.report_builder import ReportBuilder
from walletmind.exceptions import NoTransactionsForStatementError
from walletmind.schemas.transaction import TransactionDTO


class StubTransactionService:
    def __init__(self, transactions: list[TransactionDTO]) -> None:
        self._transactions = transactions

    def get_statement_transactions(self, *, statement_uuid):
        return self._transactions


class StubExecutiveSummaryBuilder:
    def __init__(self, *, raise_error: bool = False) -> None:
        self.raise_error = raise_error
        self.calls = 0

    def generate(self, *, deterministic_sections):
        self.calls += 1
        if self.raise_error:
            raise AIServiceError("Gemini timeout")
        return ExecutiveSummaryResult(
            executive_summary="Monthly profile is improving with stable cash flow.",
            strengths=["Healthy savings trend"],
            risks=["Food spending concentration"],
            action_plan=[
                "Set weekly category budget",
                "Reduce non-essential purchases",
                "Track savings target weekly",
            ],
            model="gemini-2.5-flash",
            prompt_tokens=140,
            completion_tokens=120,
            total_tokens=260,
            finish_reason="stop",
        )


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
        flags={
            "is_income": tx_type == "credit",
            "is_expense": tx_type == "debit",
            "is_subscription": False,
            "is_recurring": False,
        },
        raw_row_json={},
        created_at=datetime.now(UTC),
    )


def test_generate_monthly_report_success() -> None:
    transactions = [
        _tx(
            amount="5000.00",
            tx_type="credit",
            tx_date=date(2026, 1, 1),
            category="Income",
        ),
        _tx(
            amount="-1800.00",
            tx_type="debit",
            tx_date=date(2026, 1, 10),
            category="Food",
        ),
    ]
    service = FinancialReportService(
        transaction_service=StubTransactionService(transactions),
        report_builder=ReportBuilder(),
        executive_summary_builder=StubExecutiveSummaryBuilder(),
    )

    result = service.generate_monthly_report(statement_uuid=uuid4())

    assert result.executive_summary.startswith("Monthly profile")
    assert len(result.action_plan) == 3
    assert (
        result.health_score["overall_score"] == result.financial_health["overall_score"]
    )
    assert "overall_potential_savings" in result.budget_recommendations


def test_generate_monthly_report_ai_fallback() -> None:
    transactions = [
        _tx(
            amount="4000.00",
            tx_type="credit",
            tx_date=date(2026, 1, 1),
            category="Income",
        ),
        _tx(
            amount="-2200.00",
            tx_type="debit",
            tx_date=date(2026, 1, 20),
            category="Rent",
        ),
    ]
    service = FinancialReportService(
        transaction_service=StubTransactionService(transactions),
        report_builder=ReportBuilder(),
        executive_summary_builder=StubExecutiveSummaryBuilder(raise_error=True),
    )

    result = service.generate_monthly_report(statement_uuid=uuid4())

    assert result.executive_summary
    assert len(result.action_plan) == 3
    assert result.risks


def test_generate_monthly_report_empty_statement_raises() -> None:
    service = FinancialReportService(
        transaction_service=StubTransactionService([]),
        report_builder=ReportBuilder(),
        executive_summary_builder=StubExecutiveSummaryBuilder(),
    )

    with pytest.raises(NoTransactionsForStatementError):
        service.generate_monthly_report(statement_uuid=uuid4())


def test_generate_monthly_report_large_statement() -> None:
    transactions: list[TransactionDTO] = []
    for month in range(1, 13):
        transactions.append(
            _tx(
                amount="7000.00",
                tx_type="credit",
                tx_date=date(2026, month, 1),
                category="Income",
            )
        )
        for day in range(2, 22):
            transactions.append(
                _tx(
                    amount="-150.00",
                    tx_type="debit",
                    tx_date=date(2026, month, min(day, 28)),
                    category="Food",
                )
            )

    service = FinancialReportService(
        transaction_service=StubTransactionService(transactions),
        report_builder=ReportBuilder(),
        executive_summary_builder=StubExecutiveSummaryBuilder(),
    )

    result = service.generate_monthly_report(statement_uuid=uuid4())

    assert result.income_summary["total_income"] > 0
    assert result.expense_summary["total_expenses"] > 0
    assert result.cash_flow["monthly_trend"]
