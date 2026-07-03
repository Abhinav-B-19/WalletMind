"""Service orchestration for deterministic financial health score + AI explanation."""

from __future__ import annotations

import logging
import time
from uuid import UUID

from pydantic import BaseModel, Field

from backend.app.services.ai.ai_service import AIService
from backend.app.services.health.health_score_calculator import (
    HealthScoreCalculator,
    HealthScoreComponents,
)
from backend.app.services.health.score_explainer import ScoreExplainer
from walletmind.exceptions import NoTransactionsForStatementError
from walletmind.services.transaction_service import TransactionService


class FinancialHealthScoreResult(BaseModel):
    """API response payload for financial health score endpoint."""

    overall_score: int = Field(..., ge=0, le=100)
    grade: str
    components: HealthScoreComponents
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    ai_explanation: str
    recommendations: list[str] = Field(default_factory=list)


class FinancialHealthService:
    """Build deterministic score and AI explanation for a statement."""

    def __init__(
        self,
        *,
        transaction_service: TransactionService,
        ai_service: AIService,
        calculator: HealthScoreCalculator | None = None,
        explainer: ScoreExplainer | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._transaction_service = transaction_service
        self._ai_service = ai_service
        self._calculator = calculator or HealthScoreCalculator()
        self._explainer = explainer or ScoreExplainer()
        self._logger = logger or logging.getLogger(__name__)

    def generate_statement_health_score(
        self,
        *,
        statement_uuid: UUID,
    ) -> FinancialHealthScoreResult:
        """Generate deterministic health score and AI explanation."""

        started_at = time.perf_counter()

        transactions = self._transaction_service.get_statement_transactions(
            statement_uuid=statement_uuid
        )
        if not transactions:
            raise NoTransactionsForStatementError(
                f"Statement '{statement_uuid}' has no transactions for analysis"
            )

        computation = self._calculator.calculate(
            statement_uuid=statement_uuid,
            transactions=transactions,
        )

        user_prompt = self._explainer.build_user_prompt(computation=computation)
        ai_response = self._ai_service.generate(
            system_instruction=self._explainer.system_instruction,
            user_input=user_prompt,
        )
        explanation = self._explainer.parse_ai_response(ai_response.text)

        execution_ms = int((time.perf_counter() - started_at) * 1000)
        self._logger.info(
            "Financial health score generated.",
            extra={
                "statement_uuid": str(statement_uuid),
                "overall_score": computation.overall_score,
                "grade": computation.grade,
                "execution_ms": execution_ms,
                "model": ai_response.model,
                "total_tokens": ai_response.total_tokens,
            },
        )

        return FinancialHealthScoreResult(
            overall_score=computation.overall_score,
            grade=computation.grade,
            components=computation.components,
            strengths=computation.strengths,
            weaknesses=computation.weaknesses,
            ai_explanation=explanation.explanation,
            recommendations=explanation.recommendations,
        )
