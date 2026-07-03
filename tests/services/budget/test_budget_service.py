from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from backend.app.services.ai.exceptions import AIResponseError, AIServiceError
from backend.app.services.ai.models import AIResponse
from backend.app.services.budget.budget_service import BudgetService
from walletmind.exceptions import NoTransactionsForStatementError
from walletmind.schemas.transaction import TransactionDTO


class StubTransactionService:
    def __init__(self, transactions: list[TransactionDTO]) -> None:
        self._transactions = transactions

    def get_statement_transactions(self, *, statement_uuid):
        return self._transactions


class StubAIService:
    def __init__(self, response: AIResponse | Exception) -> None:
        self._response = response
        self.calls = 0
        self.last_kwargs = None

    def generate(self, **kwargs):
        self.calls += 1
        self.last_kwargs = kwargs
        if isinstance(self._response, Exception):
            raise self._response
        return self._response


def _tx(
    *,
    tx_date: date,
    amount: str,
    tx_type: str,
    category: str,
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


def test_budget_service_generates_result_with_mocked_ai() -> None:
    transactions = [
        _tx(
            tx_date=date(2026, 1, 1),
            amount="6000.00",
            tx_type="credit",
            category="Income",
        ),
        _tx(
            tx_date=date(2026, 1, 3),
            amount="-2500.00",
            tx_type="debit",
            category="Shopping",
        ),
        _tx(
            tx_date=date(2026, 1, 10),
            amount="-1800.00",
            tx_type="debit",
            category="Food",
        ),
    ]

    ai_service = StubAIService(
        AIResponse(
            text=(
                '{"summary":"Reduce shopping and dining to increase savings.",'
                '"recommendations":["Set category caps",'
                '"Track weekly spending","Automate savings transfer"]}'
            ),
            model="gemini-2.5-flash",
            prompt_tokens=10,
            completion_tokens=12,
            total_tokens=22,
            finish_reason="stop",
        )
    )

    service = BudgetService(
        transaction_service=StubTransactionService(transactions),
        ai_service=ai_service,
    )

    result = service.generate_statement_budget_recommendations(statement_uuid=uuid4())

    assert result.overall_potential_savings >= 0
    assert result.ai_summary.startswith("Reduce")
    assert len(result.ai_recommendations) == 3
    assert ai_service.calls == 1
    assert ai_service.last_kwargs["response_mime_type"] == "application/json"
    assert ai_service.last_kwargs["response_schema"]["type"] == "object"
    assert ai_service.last_kwargs["max_output_tokens"] == 900


def test_budget_service_empty_statement_raises() -> None:
    service = BudgetService(
        transaction_service=StubTransactionService([]),
        ai_service=StubAIService(
            AIResponse(
                text='{"summary":"N/A","recommendations":[]}',
                model="gemini-2.5-flash",
                prompt_tokens=1,
                completion_tokens=1,
                total_tokens=2,
                finish_reason="stop",
            )
        ),
    )

    with pytest.raises(NoTransactionsForStatementError):
        service.generate_statement_budget_recommendations(statement_uuid=uuid4())


def test_budget_service_accepts_markdown_fenced_json() -> None:
    service = BudgetService(
        transaction_service=StubTransactionService([]),
        ai_service=StubAIService(
            AIResponse(
                text='{"summary":"unused","recommendations":[]}',
                model="gemini-2.5-flash",
                prompt_tokens=1,
                completion_tokens=1,
                total_tokens=2,
                finish_reason="stop",
            )
        ),
    )

    parsed = service._parse_ai_response(
        raw_text="""```json
{"summary":"Good plan","recommendations":["Cap dining","Track weekly","Auto-save"]}
```""",
        finish_reason="stop",
        prompt_tokens=100,
        completion_tokens=40,
        total_tokens=140,
    )

    assert parsed.summary == "Good plan"
    assert parsed.recommendations == ["Cap dining", "Track weekly", "Auto-save"]


def test_budget_service_parse_rejects_malformed_json() -> None:
    service = BudgetService(
        transaction_service=StubTransactionService([]),
        ai_service=StubAIService(
            AIResponse(
                text='{"summary":"unused","recommendations":[]}',
                model="gemini-2.5-flash",
                prompt_tokens=1,
                completion_tokens=1,
                total_tokens=2,
                finish_reason="stop",
            )
        ),
    )

    with pytest.raises(AIResponseError, match="not valid JSON"):
        service._parse_ai_response(
            raw_text='{"summary":"Missing comma" "recommendations":["A","B","C"]}',
            finish_reason="stop",
            prompt_tokens=100,
            completion_tokens=40,
            total_tokens=140,
        )


def test_budget_service_parse_rejects_truncated_json() -> None:
    service = BudgetService(
        transaction_service=StubTransactionService([]),
        ai_service=StubAIService(
            AIResponse(
                text='{"summary":"unused","recommendations":[]}',
                model="gemini-2.5-flash",
                prompt_tokens=1,
                completion_tokens=1,
                total_tokens=2,
                finish_reason="stop",
            )
        ),
    )

    with pytest.raises(AIResponseError, match="not valid JSON"):
        service._parse_ai_response(
            raw_text='{"summary":"Truncated","recommendations":["A","B","C"]',
            finish_reason="max_tokens",
            prompt_tokens=800,
            completion_tokens=220,
            total_tokens=1020,
        )


def test_budget_service_parse_rejects_missing_fields() -> None:
    service = BudgetService(
        transaction_service=StubTransactionService([]),
        ai_service=StubAIService(
            AIResponse(
                text='{"summary":"unused","recommendations":[]}',
                model="gemini-2.5-flash",
                prompt_tokens=1,
                completion_tokens=1,
                total_tokens=2,
                finish_reason="stop",
            )
        ),
    )

    with pytest.raises(AIResponseError, match="schema is invalid"):
        service._parse_ai_response(
            raw_text='{"summary":"Only summary"}',
            finish_reason="stop",
            prompt_tokens=100,
            completion_tokens=40,
            total_tokens=140,
        )


def test_budget_service_parse_rejects_non_three_recommendations() -> None:
    service = BudgetService(
        transaction_service=StubTransactionService([]),
        ai_service=StubAIService(
            AIResponse(
                text='{"summary":"unused","recommendations":[]}',
                model="gemini-2.5-flash",
                prompt_tokens=1,
                completion_tokens=1,
                total_tokens=2,
                finish_reason="stop",
            )
        ),
    )

    with pytest.raises(AIResponseError, match="schema is invalid"):
        service._parse_ai_response(
            raw_text='{"summary":"Too short","recommendations":["One","Two"]}',
            finish_reason="stop",
            prompt_tokens=100,
            completion_tokens=40,
            total_tokens=140,
        )


def test_budget_service_generate_invalid_ai_payload_uses_fallback() -> None:
    transactions = [
        _tx(
            tx_date=date(2026, 1, 1),
            amount="6000.00",
            tx_type="credit",
            category="Income",
        ),
        _tx(
            tx_date=date(2026, 1, 3),
            amount="-2500.00",
            tx_type="debit",
            category="Shopping",
        ),
    ]

    service = BudgetService(
        transaction_service=StubTransactionService(transactions),
        ai_service=StubAIService(
            AIResponse(
                text="not-json",
                model="gemini-2.5-flash",
                prompt_tokens=10,
                completion_tokens=12,
                total_tokens=22,
                finish_reason="stop",
            )
        ),
    )

    result = service.generate_statement_budget_recommendations(statement_uuid=uuid4())

    assert "AI explanation was unavailable" in result.ai_summary
    assert len(result.ai_recommendations) == 3


def test_budget_service_generate_ai_failure_uses_fallback() -> None:
    transactions = [
        _tx(
            tx_date=date(2026, 1, 1),
            amount="6000.00",
            tx_type="credit",
            category="Income",
        ),
        _tx(
            tx_date=date(2026, 1, 3),
            amount="-2500.00",
            tx_type="debit",
            category="Shopping",
        ),
    ]

    service = BudgetService(
        transaction_service=StubTransactionService(transactions),
        ai_service=StubAIService(AIServiceError("Gemini request timed out.")),
    )

    result = service.generate_statement_budget_recommendations(statement_uuid=uuid4())

    assert "AI explanation was unavailable" in result.ai_summary
    assert len(result.ai_recommendations) == 3
