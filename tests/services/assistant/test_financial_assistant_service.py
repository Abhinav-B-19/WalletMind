from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from backend.app.services.ai.models import AIResponse
from backend.app.services.assistant.context_builder import ContextBuilder
from backend.app.services.assistant.financial_assistant_service import (
    AssistantChatRequest,
    FinancialAssistantService,
)
from backend.app.services.assistant.retrieval_service import RetrievalResult
from walletmind.exceptions import AssistantNoDataError
from walletmind.schemas.transaction import TransactionDTO


class StubRetrievalService:
    def __init__(self, result: RetrievalResult):
        self._result = result

    def retrieve(self, *, statement_uuid, question):
        return self._result


class StubAIService:
    def __init__(self, response: AIResponse):
        self._response = response

    def generate(self, **kwargs):
        return self._response


def _tx() -> TransactionDTO:
    value = Decimal("-12.45")
    return TransactionDTO(
        transaction_uuid=uuid4(),
        statement_uuid=uuid4(),
        transaction_date=date(2026, 1, 5),
        description="Coffee",
        debit=value,
        credit=None,
        amount=value,
        transaction_type="debit",
        balance=None,
        currency="USD",
        reference_number=None,
        merchant_name="Starbucks",
        bank_gateway=None,
        category="Food & Dining",
        subcategory=None,
        payment_channel="Card",
        transaction_kind="expense",
        confidence_score=90,
        raw_description="Coffee",
        clean_description="coffee",
        normalized_transaction_type="expense",
        flags={"is_recurring": False},
        raw_row_json={},
        created_at=datetime.now(UTC),
    )


def test_chat_success() -> None:
    statement_id = uuid4()
    retrieval_result = RetrievalResult(
        statement_uuid=statement_id,
        question="How much at Starbucks?",
        filters_applied={"merchant": "starbucks"},
        transactions=[_tx()],
    )
    service = FinancialAssistantService(
        retrieval_service=StubRetrievalService(retrieval_result),
        context_builder=ContextBuilder(),
        ai_service=StubAIService(
            AIResponse(
                text='{"answer":"You spent $12.45 at Starbucks.","confidence":0.92}',
                model="gemini-2.5-flash",
                prompt_tokens=12,
                completion_tokens=15,
                total_tokens=27,
                finish_reason="stop",
            )
        ),
    )

    response = service.chat(
        AssistantChatRequest(
            statement_id=statement_id,
            question="How much at Starbucks?",
        )
    )

    assert response.answer == "You spent $12.45 at Starbucks."
    assert response.confidence == 0.92
    assert len(response.sources) == 1
    assert response.sources[0].merchant == "Starbucks"


def test_chat_raises_when_no_retrieved_transactions() -> None:
    statement_id = uuid4()
    retrieval_result = RetrievalResult(
        statement_uuid=statement_id,
        question="How much at Starbucks?",
        filters_applied={},
        transactions=[],
    )
    service = FinancialAssistantService(
        retrieval_service=StubRetrievalService(retrieval_result),
        context_builder=ContextBuilder(),
        ai_service=StubAIService(
            AIResponse(
                text='{"answer":"Insufficient data.","confidence":0.4}',
                model="gemini-2.5-flash",
                prompt_tokens=1,
                completion_tokens=1,
                total_tokens=2,
                finish_reason="stop",
            )
        ),
    )

    with pytest.raises(AssistantNoDataError, match="matching the requested"):
        service.chat(
            AssistantChatRequest(
                statement_id=statement_id,
                question="How much at Starbucks?",
            )
        )


@pytest.mark.parametrize(
    ("filters_applied", "question", "expected_fragment"),
    [
        (
            {"merchant": "amazon"},
            "How much did I spend on Amazon?",
            "merchant 'amazon'",
        ),
        (
            {"category": "Food & Dining"},
            "How much did I spend on food?",
            "'Food & Dining' category",
        ),
        (
            {"month": "3"},
            "How much did I spend in March 2026?",
            "March 2026",
        ),
        (
            {"recurring": "true"},
            "Show my subscriptions",
            "recurring subscription payments",
        ),
        (
            {},
            "Any unusual charges?",
            "matching the requested merchant, category, or criteria",
        ),
    ],
)
def test_chat_raises_contextual_no_data_message(
    filters_applied: dict[str, str],
    question: str,
    expected_fragment: str,
) -> None:
    statement_id = uuid4()
    retrieval_result = RetrievalResult(
        statement_uuid=statement_id,
        question=question,
        filters_applied=filters_applied,
        transactions=[],
    )
    service = FinancialAssistantService(
        retrieval_service=StubRetrievalService(retrieval_result),
        context_builder=ContextBuilder(),
        ai_service=StubAIService(
            AIResponse(
                text='{"answer":"Insufficient data.","confidence":0.4}',
                model="gemini-2.5-flash",
                prompt_tokens=1,
                completion_tokens=1,
                total_tokens=2,
                finish_reason="stop",
            )
        ),
    )

    with pytest.raises(AssistantNoDataError, match=expected_fragment):
        service.chat(
            AssistantChatRequest(
                statement_id=statement_id,
                question=question,
            )
        )
