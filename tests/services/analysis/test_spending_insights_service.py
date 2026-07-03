from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from backend.app.services.ai.exceptions import AIServiceError
from backend.app.services.ai.models import AIResponse
from backend.app.services.analysis.spending_insights_service import (
    SpendingInsightsService,
)
from walletmind.exceptions import (
    NoTransactionsForStatementError,
    StatementNotFoundError,
)
from walletmind.schemas.transaction import TransactionDTO


class StubTransactionService:
    def __init__(self, transactions: list[TransactionDTO] | Exception) -> None:
        self._transactions = transactions

    def get_statement_transactions(self, *, statement_uuid):
        if isinstance(self._transactions, Exception):
            raise self._transactions
        return self._transactions


class StubAIService:
    def __init__(self, response: AIResponse | Exception) -> None:
        self._response = response
        self.last_payload: dict[str, object] | None = None

    def generate(self, **kwargs):
        self.last_payload = kwargs
        if isinstance(self._response, Exception):
            raise self._response
        return self._response



def _tx(amount: str, tx_type: str, category: str, merchant: str) -> TransactionDTO:
    amount_decimal = Decimal(amount)
    return TransactionDTO(
        transaction_uuid=uuid4(),
        statement_uuid=uuid4(),
        transaction_date=date(2026, 1, 1),
        description="redacted",
        debit=amount_decimal if tx_type == "debit" else None,
        credit=amount_decimal if tx_type == "credit" else None,
        amount=amount_decimal,
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
            "is_subscription": merchant == "Netflix",
        },
        raw_row_json={},
        created_at=datetime.now(UTC),
    )



def test_generate_statement_insights_success() -> None:
    statement_uuid = uuid4()
    transactions = [
        _tx("3000.00", "credit", "Income", "Employer"),
        _tx("-1200.00", "debit", "Rent", "Landlord"),
    ]
    ai_response = AIResponse(
        text=(
            '{"summary":"Stable month","strengths":["Healthy savings"],'
            '"concerns":["High rent ratio"],"recommendations":['
            '{"title":"Reduce rent burden","description":"Negotiate lease",'
            '"priority":"medium"}]}'
        ),
        model="gemini-1.5-flash",
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150,
        finish_reason="stop",
    )
    service = SpendingInsightsService(
        transaction_service=StubTransactionService(transactions),
        ai_service=StubAIService(ai_response),
    )

    result = service.generate_statement_insights(statement_uuid=statement_uuid)

    assert result.statement_uuid == statement_uuid
    assert result.insights.summary == "Stable month"
    assert result.insights.recommendations[0].priority == "medium"
    assert result.total_tokens == 150
    assert service._ai_service.last_payload is not None
    assert service._ai_service.last_payload["response_mime_type"] == "application/json"
    assert service._ai_service.last_payload["response_schema"]["type"] == "object"
    assert service._ai_service.last_payload["max_output_tokens"] == 900



def test_parse_invalid_json_response_uses_fallback() -> None:
    statement_uuid = uuid4()
    transactions = [_tx("1000.00", "credit", "Income", "Employer")]
    ai_response = AIResponse(
        text="not-json",
        model="gemini",
        prompt_tokens=1,
        completion_tokens=1,
        total_tokens=2,
        finish_reason="stop",
    )
    service = SpendingInsightsService(
        transaction_service=StubTransactionService(transactions),
        ai_service=StubAIService(ai_response),
    )

    result = service.generate_statement_insights(statement_uuid=statement_uuid)

    assert result.model == "deterministic-fallback"
    assert result.finish_reason == "fallback"
    assert "AI narrative was unavailable" in result.insights.summary



def test_empty_statement_raises() -> None:
    service = SpendingInsightsService(
        transaction_service=StubTransactionService([]),
        ai_service=StubAIService(
            AIResponse(
                text="{}",
                model="gemini",
                prompt_tokens=1,
                completion_tokens=1,
                total_tokens=2,
                finish_reason="stop",
            )
        ),
    )

    with pytest.raises(NoTransactionsForStatementError):
        service.generate_statement_insights(statement_uuid=uuid4())



def test_statement_not_found_bubbles() -> None:
    service = SpendingInsightsService(
        transaction_service=StubTransactionService(
            StatementNotFoundError("missing statement")
        ),
        ai_service=StubAIService(
            AIResponse(
                text="{}",
                model="gemini",
                prompt_tokens=1,
                completion_tokens=1,
                total_tokens=2,
                finish_reason="stop",
            )
        ),
    )

    with pytest.raises(StatementNotFoundError):
        service.generate_statement_insights(statement_uuid=uuid4())



def test_gemini_timeout_uses_fallback() -> None:
    service = SpendingInsightsService(
        transaction_service=StubTransactionService(
            [_tx("1000.00", "credit", "Income", "Employer")]
        ),
        ai_service=StubAIService(AIServiceError("Gemini request timed out.")),
    )

    result = service.generate_statement_insights(statement_uuid=uuid4())

    assert result.model == "deterministic-fallback"
    assert result.finish_reason == "fallback"
