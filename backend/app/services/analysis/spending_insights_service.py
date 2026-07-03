"""AI orchestration service for statement spending insights."""

from __future__ import annotations

import json
import logging
import time
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, ValidationError

from backend.app.services.ai.ai_service import AIService
from backend.app.services.ai.exceptions import AIResponseError, AIServiceError
from backend.app.services.ai.structured_output import parse_json_response
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

    _RESPONSE_SCHEMA = {
        "type": "object",
        "required": ["summary", "strengths", "concerns", "recommendations"],
        "properties": {
            "summary": {"type": "string", "minLength": 1},
            "strengths": {
                "type": "array",
                "items": {"type": "string"},
            },
            "concerns": {
                "type": "array",
                "items": {"type": "string"},
            },
            "recommendations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["title", "description", "priority"],
                    "properties": {
                        "title": {"type": "string", "minLength": 1},
                        "description": {"type": "string", "minLength": 1},
                        "priority": {
                            "type": "string",
                            "enum": ["low", "medium", "high"],
                        },
                    },
                    "additionalProperties": False,
                },
            },
        },
        "additionalProperties": False,
    }

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

        model = "deterministic-fallback"
        prompt_tokens = 0
        completion_tokens = 0
        total_tokens = 0
        finish_reason = "fallback"

        try:
            ai_response = self._ai_service.generate(
                system_instruction=self._SYSTEM_INSTRUCTION,
                user_input=user_prompt,
                response_mime_type="application/json",
                response_schema=self._RESPONSE_SCHEMA,
                max_output_tokens=900,
            )
            parsed = self._parse_ai_response(ai_response.text)
            model = ai_response.model
            prompt_tokens = ai_response.prompt_tokens
            completion_tokens = ai_response.completion_tokens
            total_tokens = ai_response.total_tokens
            finish_reason = ai_response.finish_reason
        except (AIResponseError, AIServiceError) as exc:
            self._logger.warning(
                "Spending insights AI narrative unavailable; using deterministic fallback.",
                extra={
                    "statement_uuid": str(statement_uuid),
                    "error": str(exc),
                },
            )
            parsed = self._fallback_insights(summary)

        execution_ms = int((time.perf_counter() - started_at) * 1000)
        self._logger.info(
            "Statement insights generated.",
            extra={
                "statement_uuid": str(statement_uuid),
                "model": model,
                "execution_ms": execution_ms,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "finish_reason": finish_reason,
            },
        )

        return SpendingInsightsResult(
            statement_uuid=statement_uuid,
            deterministic_summary=summary.as_prompt_payload(),
            insights=parsed,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            finish_reason=finish_reason,
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
        parsed = parse_json_response(
            raw_text=raw_text,
            empty_error_message="AI response was empty.",
            invalid_json_error_message="AI response is not valid JSON.",
        )

        try:
            return SpendingInsightsPayload.model_validate(parsed)
        except ValidationError as exc:
            raise AIResponseError("AI response JSON schema is invalid.") from exc

    @staticmethod
    def _fallback_insights(summary: SpendingSummary) -> SpendingInsightsPayload:
        strengths: list[str] = []
        concerns: list[str] = []

        if summary.net_cash_flow >= 0:
            strengths.append("Positive net cash flow for the analyzed period.")
        else:
            concerns.append("Net cash flow is negative for the analyzed period.")

        if summary.savings_rate >= 20:
            strengths.append("Savings rate is in a healthy range.")
        else:
            concerns.append("Savings rate is below the target range.")

        recommendations: list[InsightRecommendation] = []
        for category in summary.top_spending_categories[:3]:
            recommendations.append(
                InsightRecommendation(
                    title=f"Review {category['category']} spending",
                    description=(
                        "Set a category limit and track weekly variance "
                        f"for {category['category']}."
                    ),
                    priority="medium",
                )
            )

        if not recommendations:
            recommendations.append(
                InsightRecommendation(
                    title="Track discretionary spending",
                    description="Review weekly outflows and set practical category caps.",
                    priority="medium",
                )
            )

        summary_text = (
            "AI narrative was unavailable; deterministic spending insights are shown. "
            f"Net cash flow is {float(summary.net_cash_flow):.2f} with a savings rate "
            f"of {summary.savings_rate:.1f}%."
        )

        return SpendingInsightsPayload(
            summary=summary_text,
            strengths=strengths,
            concerns=concerns,
            recommendations=recommendations,
        )
