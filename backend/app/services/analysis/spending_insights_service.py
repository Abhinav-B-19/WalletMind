"""AI orchestration service for statement spending insights."""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, ValidationError

from backend.app.services.ai.ai_service import AIService
from backend.app.services.ai.exceptions import AIResponseError
from backend.app.services.analysis.spending_summary_builder import (
    SpendingSummary,
    SpendingSummaryBuilder,
)
from walletmind.exceptions import NoTransactionsForStatementError
from walletmind.services.transaction_service import TransactionService


class InsightRecommendation(BaseModel):
    """Actionable recommendation returned by AI."""

    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    priority: str = Field(..., pattern="^(low|medium|high)$")


class SpendingInsightsPayload(BaseModel):
    """Validated AI response payload for spending insights."""

    summary: str = Field(..., min_length=1)
    strengths: list[str] = Field(default_factory=list)
    concerns: list[str] = Field(default_factory=list)
    recommendations: list[InsightRecommendation] = Field(default_factory=list)


class SpendingInsightsResult(BaseModel):
    """Final result returned to API handlers."""

    statement_uuid: UUID
    deterministic_summary: dict[str, Any]
    insights: SpendingInsightsPayload
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    finish_reason: str


class SpendingInsightsService:
    """Compose deterministic summary + AI reasoning into structured insights."""

    _SYSTEM_INSTRUCTION = (
        "You are WalletMind Financial Analyst. "
        "Use a professional, positive, and practical tone. "
        "Never invent numbers. "
        "Base reasoning only on supplied financial data. "
        "Do not provide investment, legal, or medical advice. "
        "Respond strictly as JSON with keys: "
        "summary, strengths, concerns, recommendations."
    )

    def __init__(
        self,
        *,
        transaction_service: TransactionService,
        ai_service: AIService,
        summary_builder: SpendingSummaryBuilder | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize service with injected dependencies."""

        self._transaction_service = transaction_service
        self._ai_service = ai_service
        self._summary_builder = summary_builder or SpendingSummaryBuilder()
        self._logger = logger or logging.getLogger(__name__)

    def generate_statement_insights(
        self,
        *,
        statement_uuid: UUID,
    ) -> SpendingInsightsResult:
        """Generate spending insights for a processed statement UUID."""

        started_at = time.perf_counter()

        transactions = self._transaction_service.get_statement_transactions(
            statement_uuid=statement_uuid
        )
        if not transactions:
            raise NoTransactionsForStatementError(
                f"Statement '{statement_uuid}' has no transactions for analysis"
            )

        summary = self._summary_builder.build(
            statement_uuid=statement_uuid,
            transactions=transactions,
        )

        user_prompt = self._build_user_prompt(summary)
        prompt_size = len(self._SYSTEM_INSTRUCTION) + len(user_prompt)

        self._logger.info(
            "Generating statement insights.",
            extra={
                "statement_uuid": str(statement_uuid),
                "prompt_size_chars": prompt_size,
            },
        )

        ai_response = self._ai_service.generate(
            system_instruction=self._SYSTEM_INSTRUCTION,
            user_input=user_prompt,
        )
        parsed = self._parse_ai_response(ai_response.text)

        execution_ms = int((time.perf_counter() - started_at) * 1000)
        self._logger.info(
            "Statement insights generated.",
            extra={
                "statement_uuid": str(statement_uuid),
                "model": ai_response.model,
                "execution_ms": execution_ms,
                "prompt_tokens": ai_response.prompt_tokens,
                "completion_tokens": ai_response.completion_tokens,
                "total_tokens": ai_response.total_tokens,
                "finish_reason": ai_response.finish_reason,
            },
        )

        return SpendingInsightsResult(
            statement_uuid=statement_uuid,
            deterministic_summary=summary.as_prompt_payload(),
            insights=parsed,
            model=ai_response.model,
            prompt_tokens=ai_response.prompt_tokens,
            completion_tokens=ai_response.completion_tokens,
            total_tokens=ai_response.total_tokens,
            finish_reason=ai_response.finish_reason,
        )

    def _build_user_prompt(self, summary: SpendingSummary) -> str:
        """Build compact user prompt payload from deterministic summary."""

        payload = {
            "summary": {
                "statement_uuid": str(summary.statement_uuid),
                "transaction_count": summary.transaction_count,
                "credit_count": summary.credit_count,
                "debit_count": summary.debit_count,
            },
            "cash_flow": {
                "total_income": float(summary.total_income),
                "total_expenses": float(summary.total_expenses),
                "net_cash_flow": float(summary.net_cash_flow),
                "savings_rate": summary.savings_rate,
            },
            "category_breakdown": summary.top_spending_categories,
            "merchant_breakdown": summary.top_merchants,
            "recurring_subscriptions": summary.recurring_subscriptions,
            "large_expenses": summary.largest_expense,
            "largest_income": summary.largest_income,
            "monthly_trend": summary.monthly_trend,
            "monthly_averages": summary.monthly_averages,
        }

        return (
            "Analyze the following deterministic financial summary and "
            "produce concise actionable insights.\n"
            "The response must be JSON only.\n"
            f"DATA:\n{json.dumps(payload, ensure_ascii=True, sort_keys=True)}"
        )

    def _parse_ai_response(self, raw_text: str) -> SpendingInsightsPayload:
        """Parse and validate AI JSON payload, including fenced JSON responses."""

        candidate = raw_text.strip()
        if not candidate:
            raise AIResponseError("AI response was empty.")

        match = re.search(r"```json\s*(\{.*?\})\s*```", candidate, re.DOTALL)
        if match:
            candidate = match.group(1)

        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError as exc:
            raise AIResponseError("AI response is not valid JSON.") from exc

        try:
            return SpendingInsightsPayload.model_validate(parsed)
        except ValidationError as exc:
            raise AIResponseError("AI response JSON schema is invalid.") from exc
