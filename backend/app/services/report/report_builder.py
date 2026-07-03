"""Deterministic monthly report section builder."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from backend.app.services.analysis.spending_summary_builder import (
    SpendingSummary,
    SpendingSummaryBuilder,
)
from backend.app.services.budget.budget_calculator import BudgetCalculator
from backend.app.services.budget.recommendation_prioritizer import (
    PriorityRecommendation,
    RecommendationPrioritizer,
)
from backend.app.services.health.health_score_calculator import HealthScoreCalculator
from walletmind.schemas.transaction import TransactionDTO


class DeterministicReportSections(BaseModel):
    """Deterministic sections used by the monthly report API response."""

    financial_health: dict[str, Any]
    income_summary: dict[str, Any]
    expense_summary: dict[str, Any]
    cash_flow: dict[str, Any]
    spending_insights: dict[str, Any]
    budget_recommendations: dict[str, Any]
    health_score: dict[str, Any]


@dataclass(frozen=True)
class ReportBuildResult:
    """Combined deterministic report data and reusable context objects."""

    sections: DeterministicReportSections
    summary: SpendingSummary
    prioritized_recommendations: list[PriorityRecommendation]


class ReportBuilder:
    """Build report-ready deterministic sections from existing calculators/builders."""

    def __init__(
        self,
        *,
        summary_builder: SpendingSummaryBuilder | None = None,
        health_calculator: HealthScoreCalculator | None = None,
        budget_calculator: BudgetCalculator | None = None,
        recommendation_prioritizer: RecommendationPrioritizer | None = None,
    ) -> None:
        self._summary_builder = summary_builder or SpendingSummaryBuilder()
        self._health_calculator = health_calculator or HealthScoreCalculator(
            summary_builder=self._summary_builder,
        )
        self._budget_calculator = budget_calculator or BudgetCalculator(
            summary_builder=self._summary_builder,
        )
        self._recommendation_prioritizer = (
            recommendation_prioritizer or RecommendationPrioritizer()
        )

    def build(
        self,
        *,
        statement_uuid: UUID,
        transactions: list[TransactionDTO],
    ) -> ReportBuildResult:
        """Construct deterministic sections for the monthly financial report."""

        summary = self._summary_builder.build(
            statement_uuid=statement_uuid,
            transactions=transactions,
        )
        health = self._health_calculator.calculate_from_summary(summary=summary)
        budget = self._budget_calculator.calculate_from_summary(
            summary=summary,
            health=health,
        )
        prioritized = self._recommendation_prioritizer.prioritize(
            categories=budget.category_analysis,
            health=health,
        )

        sections = DeterministicReportSections(
            financial_health={
                "overall_score": health.overall_score,
                "grade": health.grade,
                "components": health.components.model_dump(),
                "strengths": health.strengths,
                "weaknesses": health.weaknesses,
            },
            income_summary={
                "total_income": float(summary.total_income),
                "credit_count": summary.credit_count,
                "largest_income": summary.largest_income,
                "average_monthly_income": summary.monthly_averages["income"],
            },
            expense_summary={
                "total_expenses": float(summary.total_expenses),
                "debit_count": summary.debit_count,
                "largest_expense": summary.largest_expense,
                "average_monthly_expenses": summary.monthly_averages["expenses"],
                "top_spending_categories": summary.top_spending_categories,
            },
            cash_flow={
                "net_cash_flow": float(summary.net_cash_flow),
                "savings_rate": summary.savings_rate,
                "monthly_averages": summary.monthly_averages,
                "monthly_trend": summary.monthly_trend,
            },
            spending_insights={
                "transaction_count": summary.transaction_count,
                "top_spending_categories": summary.top_spending_categories,
                "top_merchants": summary.top_merchants,
                "recurring_payments": summary.recurring_subscriptions,
                "subscriptions": summary.recurring_subscriptions,
            },
            budget_recommendations={
                "monthly_budget": {
                    category: {
                        "historical": item.historical,
                        "recommended": item.recommended,
                        "potential_saving": item.potential_saving,
                    }
                    for category, item in budget.monthly_budget.items()
                },
                "overall_potential_savings": budget.overall_potential_savings,
                "overspending_categories": budget.overspending_categories,
                "underutilized_categories": budget.underutilized_categories,
                "emergency_fund_recommendation": budget.emergency_fund_recommendation,
                "priority_recommendations": [
                    recommendation.model_dump() for recommendation in prioritized
                ],
            },
            health_score={
                "overall_score": health.overall_score,
                "grade": health.grade,
                "components": health.components.model_dump(),
            },
        )

        return ReportBuildResult(
            sections=sections,
            summary=summary,
            prioritized_recommendations=prioritized,
        )
