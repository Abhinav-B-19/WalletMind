"""Deterministic monthly budget recommendation calculator."""

from __future__ import annotations

from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from backend.app.services.analysis.spending_summary_builder import (
    SpendingSummary,
    SpendingSummaryBuilder,
)
from backend.app.services.health.health_score_calculator import HealthScoreComputation
from walletmind.schemas.transaction import TransactionDTO


class CategoryBudget(BaseModel):
    """Deterministic budget recommendation for a spending category."""

    historical: float = Field(..., ge=0.0)
    recommended: float = Field(..., ge=0.0)
    potential_saving: float = Field(..., ge=0.0)


class BudgetComputation(BaseModel):
    """Deterministic budget plan with internal diagnostics."""

    monthly_budget: dict[str, CategoryBudget] = Field(default_factory=dict)
    overall_potential_savings: float = Field(..., ge=0.0)
    overspending_categories: list[str] = Field(default_factory=list)
    underutilized_categories: list[str] = Field(default_factory=list)
    emergency_fund_recommendation: float = Field(..., ge=0.0)
    discretionary_spending_allowance: float = Field(..., ge=0.0)
    category_analysis: list[dict[str, object]] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)


class BudgetCalculator:
    """Build deterministic category budgets and savings opportunities."""

    def __init__(
        self,
        *,
        summary_builder: SpendingSummaryBuilder | None = None,
    ) -> None:
        self._summary_builder = summary_builder or SpendingSummaryBuilder()

    def calculate(
        self,
        *,
        statement_uuid: UUID,
        transactions: list[TransactionDTO],
        health: HealthScoreComputation,
    ) -> BudgetComputation:
        """Compute budget recommendations using transactions and health profile."""

        summary = self._summary_builder.build(
            statement_uuid=statement_uuid,
            transactions=transactions,
        )
        return self.calculate_from_summary(summary=summary, health=health)

    def calculate_from_summary(
        self,
        *,
        summary: SpendingSummary,
        health: HealthScoreComputation,
    ) -> BudgetComputation:
        """Compute budget recommendations from precomputed summary."""

        month_count = max(len(summary.monthly_trend), 1)
        avg_monthly_income = summary.total_income / Decimal(month_count)

        category_monthly: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
        for category, amount in summary.category_totals.items():
            category_monthly[category] = amount / Decimal(month_count)

        budget_plan: dict[str, CategoryBudget] = {}
        category_analysis: list[dict[str, object]] = []

        overspending_categories: list[str] = []
        underutilized_categories: list[str] = []
        total_potential = Decimal("0")

        strictness = self._strictness_factor(health)

        for category, historical in sorted(
            category_monthly.items(),
            key=lambda item: item[1],
            reverse=True,
        ):
            if historical <= 0:
                continue

            ratio = self._safe_ratio(historical, avg_monthly_income)
            reduction_factor = self._reduction_factor(
                ratio=ratio,
                strictness=strictness,
                category=category,
            )
            recommended = self._round_money(historical * reduction_factor)
            potential = self._round_money(max(Decimal("0"), historical - recommended))
            utilization_ratio = self._safe_ratio(historical, recommended)

            budget_plan[category] = CategoryBudget(
                historical=float(self._round_money(historical)),
                recommended=float(recommended),
                potential_saving=float(potential),
            )

            category_analysis.append(
                {
                    "category": category,
                    "historical": float(self._round_money(historical)),
                    "recommended": float(recommended),
                    "potential_saving": float(potential),
                    "utilization_ratio": float(utilization_ratio),
                }
            )

            if potential > Decimal("0"):
                overspending_categories.append(category)
                total_potential += potential
            elif utilization_ratio < Decimal("0.85"):
                underutilized_categories.append(category)

        emergency_fund = self._round_money(avg_monthly_income * Decimal("0.20"))
        essential_budget = self._round_money(
            sum(category_monthly.values(), Decimal("0"))
        )
        discretionary_allowance = self._round_money(
            max(Decimal("0"), avg_monthly_income - essential_budget)
        )

        metrics = {
            "avg_monthly_income": float(self._round_money(avg_monthly_income)),
            "avg_monthly_expenses": float(self._round_money(essential_budget)),
            "month_count": month_count,
            "health_score": health.overall_score,
            "health_grade": health.grade,
            "overspending_category_count": len(overspending_categories),
            "underutilized_category_count": len(underutilized_categories),
        }

        return BudgetComputation(
            monthly_budget=budget_plan,
            overall_potential_savings=float(self._round_money(total_potential)),
            overspending_categories=overspending_categories,
            underutilized_categories=underutilized_categories,
            emergency_fund_recommendation=float(emergency_fund),
            discretionary_spending_allowance=float(discretionary_allowance),
            category_analysis=category_analysis,
            metrics=metrics,
        )

    @staticmethod
    def _strictness_factor(health: HealthScoreComputation) -> Decimal:
        score = health.overall_score
        if score < 40:
            return Decimal("1.20")
        if score < 60:
            return Decimal("1.12")
        if score < 75:
            return Decimal("1.00")
        return Decimal("0.92")

    @staticmethod
    def _reduction_factor(
        *,
        ratio: Decimal,
        strictness: Decimal,
        category: str,
    ) -> Decimal:
        normalized = category.strip().lower()

        base = Decimal("1.00")
        if ratio >= Decimal("0.35"):
            base = Decimal("0.80")
        elif ratio >= Decimal("0.20"):
            base = Decimal("0.88")
        elif ratio >= Decimal("0.10"):
            base = Decimal("0.93")

        protected_categories = {"rent", "housing", "utilities", "loan", "tax"}
        if normalized in protected_categories:
            base = max(base, Decimal("0.92"))

        adjusted = Decimal("1.00") - ((Decimal("1.00") - base) * strictness)
        return min(Decimal("1.00"), max(Decimal("0.70"), adjusted))

    @staticmethod
    def _safe_ratio(part: Decimal, whole: Decimal) -> Decimal:
        if whole <= 0:
            return Decimal("0")
        return part / whole

    @staticmethod
    def _round_money(value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
