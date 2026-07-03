"""RAG orchestration service for conversational financial assistant responses."""

from __future__ import annotations

import calendar
import json
import logging
import re
import time
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from backend.app.services.ai.ai_service import AIService
from backend.app.services.assistant.answer_validator import AnswerValidator
from backend.app.services.assistant.context_builder import (
    AssistantContext,
    ContextBuilder,
)
from backend.app.services.assistant.retrieval_service import RetrievalService
from walletmind.exceptions import AssistantNoDataError


class AssistantChatRequest(BaseModel):
    """Request payload for assistant chat endpoint."""

    statement_id: UUID
    question: str = Field(..., min_length=1, max_length=500)


class AssistantSource(BaseModel):
    """Evidence source item backing assistant answers."""

    transaction_id: str
    merchant: str
    date: str
    amount: float


class AssistantChatResponse(BaseModel):
    """Response payload for assistant chat endpoint."""

    answer: str
    sources: list[AssistantSource]
    confidence: float = Field(..., ge=0.0, le=1.0)


class FinancialAssistantService:
    """Retrieve context, generate answer, and validate grounding for chat queries."""

    _SYSTEM_INSTRUCTION = (
        "You are WalletMind's AI Financial Assistant. "
        "Answer ONLY using the supplied financial context. "
        "Never invent transactions. "
        "Never invent amounts. "
        "Never assume missing information. "
        "If the answer is unavailable, clearly state that. "
        "Return JSON with keys: answer, confidence."
    )

    def __init__(
        self,
        *,
        retrieval_service: RetrievalService,
        context_builder: ContextBuilder,
        ai_service: AIService,
        answer_validator: AnswerValidator | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._retrieval_service = retrieval_service
        self._context_builder = context_builder
        self._ai_service = ai_service
        self._answer_validator = answer_validator or AnswerValidator()
        self._logger = logger or logging.getLogger(__name__)

    def chat(self, request: AssistantChatRequest) -> AssistantChatResponse:
        """Execute deterministic retrieval + AI generation + answer validation."""

        started_at = time.perf_counter()
        retrieval = self._retrieval_service.retrieve(
            statement_uuid=request.statement_id,
            question=request.question,
        )

        if not retrieval.transactions:
            raise AssistantNoDataError(self._build_no_data_message(retrieval))

        context = self._context_builder.build(retrieval)
        user_prompt = self._build_user_prompt(request.question, context)

        self._logger.info(
            "Assistant chat request started.",
            extra={
                "statement_id": str(request.statement_id),
                "query_length": len(request.question),
                "retrieved_transaction_count": len(retrieval.transactions),
            },
        )

        ai_response = self._ai_service.generate(
            system_instruction=self._SYSTEM_INSTRUCTION,
            user_input=user_prompt,
        )

        parsed = self._parse_ai_answer(ai_response.text)
        self._answer_validator.validate(answer=parsed["answer"], context=context)

        execution_ms = int((time.perf_counter() - started_at) * 1000)
        self._logger.info(
            "Assistant chat request completed.",
            extra={
                "statement_id": str(request.statement_id),
                "execution_ms": execution_ms,
                "prompt_tokens": ai_response.prompt_tokens,
                "completion_tokens": ai_response.completion_tokens,
                "total_tokens": ai_response.total_tokens,
                "model": ai_response.model,
            },
        )

        sources = [
            AssistantSource(
                transaction_id=str(tx["transaction_id"]),
                merchant=str(tx["merchant"]),
                date=str(tx["date"]),
                amount=float(tx["amount"]),
            )
            for tx in context.transactions[:10]
        ]

        return AssistantChatResponse(
            answer=parsed["answer"],
            sources=sources,
            confidence=float(parsed.get("confidence", 0.5)),
        )

    @staticmethod
    def _build_user_prompt(question: str, context: AssistantContext) -> str:
        """Build compact prompt body from query and retrieval context."""

        payload = {
            "question": question,
            "summary": context.summary,
            "transactions": context.transactions,
        }
        return (
            "Answer the question using only the provided context. "
            "If unavailable, explicitly state you cannot determine it.\n"
            f"CONTEXT:\n{json.dumps(payload, ensure_ascii=True, sort_keys=True)}"
        )

    @staticmethod
    def _parse_ai_answer(raw_text: str) -> dict[str, Any]:
        """Parse assistant model JSON response payload."""

        candidate = raw_text.strip()
        if candidate.startswith("```"):
            candidate = candidate.strip("`")
            candidate = candidate.replace("json", "", 1).strip()

        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError as exc:
            raise AssistantNoDataError("Assistant returned malformed JSON.") from exc

        answer = str(parsed.get("answer", "")).strip()
        if not answer:
            raise AssistantNoDataError("Assistant answer is empty.")

        confidence = parsed.get("confidence", 0.5)
        try:
            parsed["confidence"] = max(0.0, min(float(confidence), 1.0))
        except Exception:
            parsed["confidence"] = 0.5

        parsed["answer"] = answer
        return parsed

    @staticmethod
    def _build_no_data_message(retrieval: Any) -> str:
        """Build a contextual no-data response from retrieval filters."""

        filters = dict(getattr(retrieval, "filters_applied", {}) or {})
        question = str(getattr(retrieval, "question", "") or "")

        if "merchant" in filters:
            merchant = filters["merchant"].strip()
            return (
                f"I couldn't find any transactions for the merchant '{merchant}' "
                "in the selected statement, so I can't provide an accurate "
                "answer based only on your uploaded financial data."
            )

        if "category" in filters:
            category = filters["category"].strip()
            return (
                f"I couldn't find any transactions in the '{category}' category "
                "in the selected statement, so I can't provide an accurate "
                "answer based only on your uploaded financial data."
            )

        if "month" in filters:
            month_value = int(filters["month"])
            month_name = calendar.month_name[month_value]
            year = FinancialAssistantService._extract_year_from_question(question)
            period = f"{month_name} {year}" if year else month_name
            return (
                f"I couldn't find any transactions for {period} in the selected "
                "statement, so I can't provide an accurate answer based only on "
                "your uploaded financial data."
            )

        if "recurring" in filters:
            return (
                "I couldn't identify any recurring subscription payments in the "
                "selected statement, so I can't provide an accurate answer based "
                "only on your uploaded financial data."
            )

        return (
            "I couldn't find any transactions matching the requested merchant, "
            "category, or criteria in the selected statement, so I can't provide "
            "an accurate answer. Please try a different merchant name, category, "
            "or date range."
        )

    @staticmethod
    def _extract_year_from_question(question: str) -> str | None:
        """Extract a four-digit year from user question text when present."""

        year_match = re.search(r"\b(19\d{2}|20\d{2}|21\d{2})\b", question)
        if year_match:
            return year_match.group(1)
        return None
