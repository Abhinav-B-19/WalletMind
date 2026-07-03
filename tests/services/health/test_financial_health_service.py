from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from backend.app.services.ai.models import AIResponse
from backend.app.services.health.financial_health_service import FinancialHealthService
from walletmind.exceptions import NoTransactionsForStatementError
from walletmind.schemas.transaction import TransactionDTO


class StubTransactionService:
    def __init__(self, transactions: list[TransactionDTO]) -> None:
        self._transactions = transactions

    def get_statement_transactions(self, *, statement_uuid):
        return self._transactions


class StubAIService:
    def __init__(self, response: AIResponse) -> None:
        self._response = response
        self.calls = 0

    def generate(self, **kwargs):
        self.calls += 1
        return self._response


def _tx(*, amount: str, tx_type: str, tx_date: date) -> TransactionDTO:
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
        category="Income" if tx_type == "credit" else "Expense",
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


def test_generate_health_score_success_with_mocked_ai() -> None:
    statement_uuid = uuid4()
    transactions = [
        _tx(amount="5000.00", tx_type="credit", tx_date=date(2026, 1, 1)),
        _tx(amount="-1800.00", tx_type="debit", tx_date=date(2026, 1, 10)),
        _tx(amount="5000.00", tx_type="credit", tx_date=date(2026, 2, 1)),
        _tx(amount="-1500.00", tx_type="debit", tx_date=date(2026, 2, 10)),
    ]
    ai_service = StubAIService(
        AIResponse(
            text=(
                '{"explanation":"Your score is driven by strong savings and '
                'stable cash flow.","recommendations":'
                '["Reduce recurring bills"]}'
            ),
            model="gemini-2.5-flash",
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30,
            finish_reason="stop",
        )
    )

    service = FinancialHealthService(
        transaction_service=StubTransactionService(transactions),
        ai_service=ai_service,
    )

    result = service.generate_statement_health_score(statement_uuid=statement_uuid)

    assert 0 <= result.overall_score <= 100
    assert result.grade
    assert result.ai_explanation.startswith("Your score is")
    assert result.recommendations == ["Reduce recurring bills"]
    assert ai_service.calls == 1


def test_empty_statement_raises() -> None:
    service = FinancialHealthService(
        transaction_service=StubTransactionService([]),
        ai_service=StubAIService(
            AIResponse(
                text='{"explanation":"N/A","recommendations":[]}',
                model="gemini-2.5-flash",
                prompt_tokens=1,
                completion_tokens=1,
                total_tokens=2,
                finish_reason="stop",
            )
        ),
    )

    with pytest.raises(NoTransactionsForStatementError):
        service.generate_statement_health_score(statement_uuid=uuid4())


def test_income_only_statement() -> None:
    service = FinancialHealthService(
        transaction_service=StubTransactionService(
            [
                _tx(amount="4000.00", tx_type="credit", tx_date=date(2026, 1, 1)),
                _tx(amount="4100.00", tx_type="credit", tx_date=date(2026, 2, 1)),
            ]
        ),
        ai_service=StubAIService(
            AIResponse(
                text=(
                    '{"explanation":"Strong income and no expenses '
                    'recorded.","recommendations":'
                    '["Track discretionary expenses"]}'
                ),
                model="gemini-2.5-flash",
                prompt_tokens=2,
                completion_tokens=2,
                total_tokens=4,
                finish_reason="stop",
            )
        ),
    )

    result = service.generate_statement_health_score(statement_uuid=uuid4())

    assert result.components.savings_rate >= 90
    assert result.components.cash_flow >= 70


def test_expense_only_statement() -> None:
    service = FinancialHealthService(
        transaction_service=StubTransactionService(
            [
                _tx(amount="-1200.00", tx_type="debit", tx_date=date(2026, 1, 5)),
                _tx(amount="-800.00", tx_type="debit", tx_date=date(2026, 1, 20)),
            ]
        ),
        ai_service=StubAIService(
            AIResponse(
                text=(
                    '{"explanation":"No income detected in this statement '
                    'period.","recommendations":'
                    '["Add all income accounts"]}'
                ),
                model="gemini-2.5-flash",
                prompt_tokens=2,
                completion_tokens=2,
                total_tokens=4,
                finish_reason="stop",
            )
        ),
    )

    result = service.generate_statement_health_score(statement_uuid=uuid4())

    assert result.components.savings_rate == 0
    assert result.components.income_stability == 0
