"""Service orchestration for AI-powered monthly financial reports."""

from __future__ import annotations

import logging
import time
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from backend.app.services.ai.exceptions import AIResponseError, AIServiceError
from backend.app.services.report.executive_summary_builder import (
    ExecutiveSummaryBuilder,
    ExecutiveSummaryResult,
)
from backend.app.services.report.report_builder import ReportBuilder
from walletmind.exceptions import NoTransactionsForStatementError
from walletmind.services.transaction_service import TransactionService


class MonthlyFinancialReportResult(BaseModel):
    """API response payload for monthly financial report endpoint."""

    executive_summary: str
    financial_health: dict[str, Any]
    income_summary: dict[str, Any]
    expense_summary: dict[str, Any]
    cash_flow: dict[str, Any]
    spending_insights: dict[str, Any]
    budget_recommendations: dict[str, Any]
    health_score: dict[str, Any]
    strengths: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    action_plan: list[str] = Field(default_factory=list)


class FinancialReportService:
    """Build deterministic monthly report and enrich with AI executive narrative."""

    def __init__(
        self,
        *,
        transaction_service: TransactionService,
        report_builder: ReportBuilder,
        executive_summary_builder: ExecutiveSummaryBuilder,
        logger: logging.Logger | None = None,
    ) -> None:
        self._transaction_service = transaction_service
        self._report_builder = report_builder
        self._executive_summary_builder = executive_summary_builder
        self._logger = logger or logging.getLogger(__name__)

    def generate_monthly_report(
        self,
        *,
        statement_uuid: UUID,
    ) -> MonthlyFinancialReportResult:
        """Generate monthly financial report with deterministic + AI sections."""

        started_at = time.perf_counter()

        transactions = self._transaction_service.get_statement_transactions(
            statement_uuid=statement_uuid,
        )
        if not transactions:
            raise NoTransactionsForStatementError(
                f"Statement '{statement_uuid}' has no transactions for analysis"
            )

        deterministic = self._report_builder.build(
            statement_uuid=statement_uuid,
            transactions=transactions,
        )

        ai_started = time.perf_counter()
        try:
            executive = self._executive_summary_builder.generate(
                deterministic_sections=deterministic.sections.model_dump()
            )
        except (AIResponseError, AIServiceError) as exc:
            self._logger.warning(
                "Monthly report AI summary unavailable; using deterministic fallback.",
                extra={
                    "statement_uuid": str(statement_uuid),
                    "error": str(exc),
                },
            )
            executive = self._fallback_executive(
                deterministic_sections=deterministic.sections.model_dump()
            )
        ai_elapsed_ms = int((time.perf_counter() - ai_started) * 1000)

        total_execution_ms = int((time.perf_counter() - started_at) * 1000)
        self._logger.info(
            "Monthly financial report generated.",
            extra={
                "statement_uuid": str(statement_uuid),
                "execution_ms": total_execution_ms,
                "ai_execution_ms": ai_elapsed_ms,
                "model": executive.model,
                "finish_reason": executive.finish_reason,
                "prompt_tokens": executive.prompt_tokens,
                "completion_tokens": executive.completion_tokens,
                "total_tokens": executive.total_tokens,
            },
        )

        sections = deterministic.sections
        return MonthlyFinancialReportResult(
            executive_summary=executive.executive_summary,
            financial_health=sections.financial_health,
            income_summary=sections.income_summary,
            expense_summary=sections.expense_summary,
            cash_flow=sections.cash_flow,
            spending_insights=sections.spending_insights,
            budget_recommendations=sections.budget_recommendations,
            health_score=sections.health_score,
            strengths=executive.strengths,
            risks=executive.risks,
            action_plan=executive.action_plan,
        )

    @staticmethod
    def _fallback_executive(
        *,
        deterministic_sections: dict[str, Any],
    ) -> ExecutiveSummaryResult:
        health = deterministic_sections["health_score"]
        budget = deterministic_sections["budget_recommendations"]
        cash_flow = deterministic_sections["cash_flow"]

        return ExecutiveSummaryResult(
            executive_summary=(
                f"Overall financial health is {health.get('grade')} with score "
                f"{health.get('overall_score')}. Net cash flow is "
                f"{cash_flow.get('net_cash_flow')}, with potential monthly savings "
                f"of {budget.get('overall_potential_savings')}."
            ),
            strengths=[
                (
                    "Deterministic health and cash flow metrics were "
                    "generated successfully."
                ),
                (
                    "Top spending and recurring payment patterns are "
                    "available for planning."
                ),
            ],
            risks=[
                "AI narrative was unavailable; review deterministic sections directly.",
            ],
            action_plan=[
                "Prioritize the top budget recommendation this month.",
                "Review overspending categories and set weekly limits.",
                "Track savings-rate trend against your health score next cycle.",
            ],
            model="deterministic-fallback",
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            finish_reason="fallback",
        )
