"""Service orchestration for deterministic budget recommendations + AI guidance."""

from __future__ import annotations

import json
import logging
import time
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field, ValidationError

from backend.app.services.ai.ai_service import AIService
from backend.app.services.ai.exceptions import AIResponseError
from backend.app.services.analysis.spending_summary_builder import (
    SpendingSummaryBuilder,
)
from backend.app.services.budget.budget_calculator import BudgetCalculator
from backend.app.services.budget.recommendation_prioritizer import (
    PriorityRecommendation,
    RecommendationPrioritizer,
)
from backend.app.services.health.health_score_calculator import HealthScoreCalculator
from walletmind.exceptions import NoTransactionsForStatementError
from walletmind.services.transaction_service import TransactionService


class BudgetAIExplanation(BaseModel):
    """AI explanation payload for budget recommendation results."""

    summary: str = Field(..., min_length=1, max_length=280)
    recommendations: list[Annotated[str, Field(min_length=1, max_length=120)]] = Field(
        ...,
        min_length=3,
        max_length=3,
    )


class BudgetRecommendationResult(BaseModel):
    """API response payload for budget recommendation endpoint."""

    monthly_budget: dict[str, dict[str, float]] = Field(default_factory=dict)
    overall_potential_savings: float = Field(..., ge=0.0)
    priority_recommendations: list[PriorityRecommendation] = Field(default_factory=list)
    ai_summary: str
    ai_recommendations: list[str] = Field(default_factory=list)


class BudgetService:
    """Generate deterministic budget recommendations and AI explanation."""

    _RESPONSE_SCHEMA = {
        "type": "object",
        "required": ["summary", "recommendations"],
        "properties": {
            "summary": {
                "type": "string",
                "minLength": 1,
                "maxLength": 280,
            },
            "recommendations": {
                "type": "array",
                "minItems": 3,
                "maxItems": 3,
                "items": {"type": "string"},
            },
        },
        "additionalProperties": False,
    }

    _SYSTEM_INSTRUCTION = (
        "You are WalletMind Budget Coach. "
        "Use only provided deterministic numbers. "
        "Never change budget values. "
        "Never invent amounts. "
        "Do not recommend stocks, mutual funds, crypto, loans, or insurance products. "
        "Focus on spending control, savings habits, emergency fund discipline, and "
        "practical budgeting behaviors. "
        "Keep output concise. "
        "Output must be a single JSON object only. "
        "Do not include markdown, code fences, prose before JSON, or prose after JSON. "
        "Return exactly this schema: "
        '{"summary": string, "recommendations": [string, string, string]}. '
        "Summary must be one short paragraph (max 280 chars). "
        "Recommendations must be exactly 3 concise items (max 120 chars each). "
        "Do not include additional keys."
    )

    def __init__(
        self,
        *,
        transaction_service: TransactionService,
        ai_service: AIService,
        summary_builder: SpendingSummaryBuilder | None = None,
        health_calculator: HealthScoreCalculator | None = None,
        budget_calculator: BudgetCalculator | None = None,
        prioritizer: RecommendationPrioritizer | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._transaction_service = transaction_service
        self._ai_service = ai_service
        self._summary_builder = summary_builder or SpendingSummaryBuilder()
        self._health_calculator = health_calculator or HealthScoreCalculator(
            summary_builder=self._summary_builder,
        )
        self._budget_calculator = budget_calculator or BudgetCalculator(
            summary_builder=self._summary_builder,
        )
        self._prioritizer = prioritizer or RecommendationPrioritizer()
        self._logger = logger or logging.getLogger(__name__)

    def generate_statement_budget_recommendations(
        self,
        *,
        statement_uuid: UUID,
    ) -> BudgetRecommendationResult:
        """Generate deterministic budget recommendations for a statement."""

        started_at = time.perf_counter()

        transactions = self._transaction_service.get_statement_transactions(
            statement_uuid=statement_uuid,
        )
        if not transactions:
            raise NoTransactionsForStatementError(
                f"Statement '{statement_uuid}' has no transactions for analysis"
            )

        summary = self._summary_builder.build(
            statement_uuid=statement_uuid,
            transactions=transactions,
        )
        health = self._health_calculator.calculate_from_summary(summary=summary)
        budget = self._budget_calculator.calculate_from_summary(
            summary=summary,
            health=health,
        )
        prioritized = self._prioritizer.prioritize(
            categories=budget.category_analysis,
            health=health,
        )

        ai_prompt = self._build_user_prompt(
            health=health,
            budget=budget,
            priority_recommendations=prioritized,
            summary_payload=summary.as_prompt_payload(),
        )

        ai_started = time.perf_counter()
        ai_response = self._ai_service.generate(
            system_instruction=self._SYSTEM_INSTRUCTION,
            user_input=ai_prompt,
            response_mime_type="application/json",
            response_schema=self._RESPONSE_SCHEMA,
            max_output_tokens=220,
        )

        ai_elapsed_ms = int((time.perf_counter() - ai_started) * 1000)
        ai_parsed = self._parse_ai_response(
            raw_text=ai_response.text,
            finish_reason=ai_response.finish_reason,
            prompt_tokens=ai_response.prompt_tokens,
            completion_tokens=ai_response.completion_tokens,
            total_tokens=ai_response.total_tokens,
        )

        total_execution_ms = int((time.perf_counter() - started_at) * 1000)
        self._logger.info(
            "Budget recommendations generated.",
            extra={
                "statement_uuid": str(statement_uuid),
                "health_score": health.overall_score,
                "categories_analyzed": len(budget.category_analysis),
                "budget_categories_generated": len(budget.monthly_budget),
                "ai_execution_ms": ai_elapsed_ms,
                "execution_ms": total_execution_ms,
                "model": ai_response.model,
                "finish_reason": ai_response.finish_reason,
                "prompt_tokens": ai_response.prompt_tokens,
                "completion_tokens": ai_response.completion_tokens,
                "total_tokens": ai_response.total_tokens,
                "prompt_characters": len(ai_prompt),
            },
        )

        monthly_budget = {
            category: {
                "historical": float(values.historical),
                "recommended": float(values.recommended),
                "potential_saving": float(values.potential_saving),
            }
            for category, values in budget.monthly_budget.items()
        }

        return BudgetRecommendationResult(
            monthly_budget=monthly_budget,
            overall_potential_savings=budget.overall_potential_savings,
            priority_recommendations=prioritized,
            ai_summary=ai_parsed.summary,
            ai_recommendations=ai_parsed.recommendations,
        )

    def _build_user_prompt(
        self,
        *,
        health,
        budget,
        priority_recommendations: list[PriorityRecommendation],
        summary_payload: dict[str, object],
    ) -> str:
        payload = {
            "overall_health_score": health.overall_score,
            "health_grade": health.grade,
            "top_spending_categories": summary_payload.get(
                "top_spending_categories",
                [],
            )[:5],
            "top_overspending_categories": budget.overspending_categories[:5],
            "overall_potential_savings": budget.overall_potential_savings,
            "emergency_fund_recommendation": budget.emergency_fund_recommendation,
            "priority_recommendations": [
                recommendation.model_dump()
                for recommendation in priority_recommendations[:3]
            ],
        }
        return (
            "Explain why these deterministic budgets are recommended, which budget "
            "changes should be prioritized first, and practical budgeting actions.\n"
            "Keep the output short and direct.\n"
            "Return only a single JSON object matching this exact schema and nothing "
            'else: {"summary": string, "recommendations": [string, string, string]}.\n'
            "Forbidden: markdown, bullet lists, code fences, commentary outside JSON.\n"
            f"DATA:\n{json.dumps(payload, ensure_ascii=True, sort_keys=True)}"
        )

    def _parse_ai_response(
        self,
        *,
        raw_text: str,
        finish_reason: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
    ) -> BudgetAIExplanation:
        candidate = raw_text.strip()
        if not candidate:
            raise AIResponseError("Budget AI response was empty.")

        candidate = self._unwrap_json_fence(candidate)

        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError as exc:
            self._logger.error(
                "Budget AI JSON decode failed.",
                extra={
                    "error": str(exc),
                    "raw_model_response": raw_text,
                    "finish_reason": finish_reason,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                },
            )
            raise AIResponseError(
                f"Budget AI response is not valid JSON: {exc.msg}."
            ) from exc

        try:
            return BudgetAIExplanation.model_validate(parsed)
        except ValidationError as exc:
            self._logger.error(
                "Budget AI schema validation failed.",
                extra={
                    "error": str(exc),
                    "raw_model_response": raw_text,
                    "finish_reason": finish_reason,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                },
            )
            raise AIResponseError("Budget AI response schema is invalid.") from exc

    @staticmethod
    def _unwrap_json_fence(candidate: str) -> str:
        stripped = candidate.strip()
        if not stripped.startswith("```"):
            return stripped

        lines = stripped.splitlines()
        if len(lines) < 3:
            return stripped

        opening_fence = lines[0].strip().lower()
        closing_fence = lines[-1].strip()
        if closing_fence != "```":
            return stripped
        if opening_fence not in {"```", "```json"}:
            return stripped

        return "\n".join(lines[1:-1]).strip()
