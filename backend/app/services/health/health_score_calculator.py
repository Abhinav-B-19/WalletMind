"""Deterministic financial health score calculator."""

from __future__ import annotations

from decimal import Decimal
from math import sqrt
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from backend.app.services.analysis.spending_summary_builder import (
    SpendingSummary,
    SpendingSummaryBuilder,
)
from walletmind.schemas.transaction import TransactionDTO


class HealthScoreComponents(BaseModel):
    """Sub-scores contributing to the final financial health score."""

    savings_rate: int = Field(..., ge=0, le=100)
    income_stability: int = Field(..., ge=0, le=100)
    spending_discipline: int = Field(..., ge=0, le=100)
    recurring_obligations: int = Field(..., ge=0, le=100)
    cash_flow: int = Field(..., ge=0, le=100)


class HealthScoreComputation(BaseModel):
    """Deterministic score result with internal metrics for AI explanation."""

    overall_score: int = Field(..., ge=0, le=100)
    grade: str
    components: HealthScoreComponents
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)


class HealthScoreCalculator:
    """Calculate deterministic health score and component breakdown."""

    _WEIGHTS = {
        "savings_rate": Decimal("0.30"),
        "income_stability": Decimal("0.20"),
        "spending_discipline": Decimal("0.20"),
        "recurring_obligations": Decimal("0.15"),
        "cash_flow": Decimal("0.15"),
    }

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
    ) -> HealthScoreComputation:
        """Compute weighted score and deterministic diagnostics."""

        summary = self._summary_builder.build(
            statement_uuid=statement_uuid,
            transactions=transactions,
        )
        return self.calculate_from_summary(summary=summary)

    def calculate_from_summary(
        self,
        *,
        summary: SpendingSummary,
    ) -> HealthScoreComputation:
        """Compute weighted score and diagnostics from prebuilt summary."""

        monthly_income_values = [
            Decimal(str(item["income"])) for item in summary.monthly_trend
        ]
        monthly_expense_values = [
            Decimal(str(item["expenses"])) for item in summary.monthly_trend
        ]
        monthly_net_values = [
            Decimal(str(item["net"])) for item in summary.monthly_trend
        ]

        total_income = summary.total_income
        total_expenses = summary.total_expenses
        net_cash_flow = summary.net_cash_flow

        recurring_total = sum(
            Decimal(str(item.get("amount", 0)))
            for item in summary.recurring_subscriptions
        )
        largest_category_pct = self._largest_category_pct(summary)
        expense_ratio_pct = self._safe_pct(total_expenses, total_income)
        recurring_ratio_pct = self._safe_pct(recurring_total, total_income)
        positive_month_ratio_pct = self._positive_month_ratio(monthly_net_values)

        components = HealthScoreComponents(
            savings_rate=self._score_savings_rate(summary.savings_rate, total_income),
            income_stability=self._score_income_stability(monthly_income_values),
            spending_discipline=self._score_spending_discipline(
                expense_ratio_pct=expense_ratio_pct,
                largest_category_pct=largest_category_pct,
            ),
            recurring_obligations=self._score_recurring_obligations(
                recurring_ratio_pct=recurring_ratio_pct,
                total_income=total_income,
                recurring_total=recurring_total,
            ),
            cash_flow=self._score_cash_flow(
                positive_month_ratio_pct=positive_month_ratio_pct,
                net_cash_flow=net_cash_flow,
                total_income=total_income,
                total_expenses=total_expenses,
            ),
        )

        overall_score = self._weighted_score(components)
        grade = self._grade_for_score(overall_score)

        metrics = {
            "total_income": float(total_income),
            "total_expenses": float(total_expenses),
            "net_cash_flow": float(net_cash_flow),
            "savings_rate_pct": round(summary.savings_rate, 2),
            "expense_ratio_pct": round(float(expense_ratio_pct), 2),
            "recurring_expense_total": float(recurring_total),
            "recurring_ratio_pct": round(float(recurring_ratio_pct), 2),
            "largest_category_pct": round(float(largest_category_pct), 2),
            "positive_month_ratio_pct": round(float(positive_month_ratio_pct), 2),
            "monthly_income_values": [float(v) for v in monthly_income_values],
            "monthly_expense_values": [float(v) for v in monthly_expense_values],
            "monthly_net_values": [float(v) for v in monthly_net_values],
            "top_spending_categories": summary.top_spending_categories,
            "top_merchants": summary.top_merchants,
            "recurring_subscriptions": summary.recurring_subscriptions,
            "transaction_count": summary.transaction_count,
        }

        strengths, weaknesses = self._strengths_and_weaknesses(components)

        return HealthScoreComputation(
            overall_score=overall_score,
            grade=grade,
            components=components,
            strengths=strengths,
            weaknesses=weaknesses,
            metrics=metrics,
        )

    @classmethod
    def _weighted_score(cls, components: HealthScoreComponents) -> int:
        total = (
            Decimal(components.savings_rate) * cls._WEIGHTS["savings_rate"]
            + Decimal(components.income_stability) * cls._WEIGHTS["income_stability"]
            + Decimal(components.spending_discipline)
            * cls._WEIGHTS["spending_discipline"]
            + Decimal(components.recurring_obligations)
            * cls._WEIGHTS["recurring_obligations"]
            + Decimal(components.cash_flow) * cls._WEIGHTS["cash_flow"]
        )
        return cls._clamp_score(int(round(float(total))))

    @staticmethod
    def _grade_for_score(score: int) -> str:
        if score >= 90:
            return "Excellent"
        if score >= 75:
            return "Good"
        if score >= 60:
            return "Fair"
        if score >= 40:
            return "Needs Improvement"
        return "Critical"

    @classmethod
    def _score_savings_rate(cls, savings_rate_pct: float, total_income: Decimal) -> int:
        if total_income <= 0:
            return 0
        baseline = max(0.0, min(100.0, savings_rate_pct))
        return cls._clamp_score(int(round(baseline)))

    @classmethod
    def _score_income_stability(cls, monthly_income_values: list[Decimal]) -> int:
        incomes = [value for value in monthly_income_values if value > 0]
        if not incomes:
            return 0
        if len(incomes) == 1:
            return 80

        mean_income = sum(incomes, Decimal("0")) / Decimal(len(incomes))
        if mean_income <= 0:
            return 0

        variance = sum((value - mean_income) ** 2 for value in incomes) / Decimal(
            len(incomes)
        )
        std_dev = Decimal(str(sqrt(float(variance))))
        cv = std_dev / mean_income

        score = 100 - int(round(min(100.0, float(cv) * 120.0)))
        return cls._clamp_score(score)

    @classmethod
    def _score_spending_discipline(
        cls,
        *,
        expense_ratio_pct: Decimal,
        largest_category_pct: Decimal,
    ) -> int:
        ratio_score = cls._clamp_score(
            int(round(100 - max(0.0, float(expense_ratio_pct) - 50.0) * 1.5))
        )
        concentration_score = cls._clamp_score(
            int(round(100 - max(0.0, float(largest_category_pct) - 35.0) * 1.3))
        )
        composite = int(round((ratio_score * 0.65) + (concentration_score * 0.35)))
        return cls._clamp_score(composite)

    @classmethod
    def _score_recurring_obligations(
        cls,
        *,
        recurring_ratio_pct: Decimal,
        total_income: Decimal,
        recurring_total: Decimal,
    ) -> int:
        if total_income <= 0 and recurring_total > 0:
            return 0
        if recurring_total <= 0:
            return 100
        score = 100 - int(round(float(recurring_ratio_pct) * 1.8))
        return cls._clamp_score(score)

    @classmethod
    def _score_cash_flow(
        cls,
        *,
        positive_month_ratio_pct: Decimal,
        net_cash_flow: Decimal,
        total_income: Decimal,
        total_expenses: Decimal,
    ) -> int:
        if total_income <= 0 and total_expenses > 0:
            return 10

        margin_pct = cls._safe_pct(net_cash_flow, total_income)
        margin_score = cls._clamp_score(int(round(50 + float(margin_pct))))
        composite = int(
            round((float(positive_month_ratio_pct) * 0.6) + (margin_score * 0.4))
        )
        return cls._clamp_score(composite)

    @staticmethod
    def _safe_pct(part: Decimal, whole: Decimal) -> Decimal:
        if whole <= 0:
            return Decimal("0")
        return (part / whole) * Decimal("100")

    @staticmethod
    def _positive_month_ratio(monthly_nets: list[Decimal]) -> Decimal:
        if not monthly_nets:
            return Decimal("0")
        positive = sum(1 for value in monthly_nets if value >= 0)
        return (Decimal(positive) / Decimal(len(monthly_nets))) * Decimal("100")

    @staticmethod
    def _largest_category_pct(summary: SpendingSummary) -> Decimal:
        if summary.total_expenses <= 0 or not summary.top_spending_categories:
            return Decimal("0")
        largest_amount = Decimal(str(summary.top_spending_categories[0]["amount"]))
        return (largest_amount / summary.total_expenses) * Decimal("100")

    @staticmethod
    def _strengths_and_weaknesses(
        components: HealthScoreComponents,
    ) -> tuple[list[str], list[str]]:
        labels = {
            "savings_rate": "Healthy savings behavior",
            "income_stability": "Stable income pattern",
            "spending_discipline": "Disciplined spending pattern",
            "recurring_obligations": "Manageable recurring obligations",
            "cash_flow": "Positive cash flow trend",
        }

        scored = [
            ("savings_rate", components.savings_rate),
            ("income_stability", components.income_stability),
            ("spending_discipline", components.spending_discipline),
            ("recurring_obligations", components.recurring_obligations),
            ("cash_flow", components.cash_flow),
        ]

        strengths = [labels[name] for name, score in scored if score >= 75]
        weaknesses = [labels[name] for name, score in scored if score < 60]

        if not strengths:
            top_name = max(scored, key=lambda item: item[1])[0]
            strengths = [labels[top_name]]
        if not weaknesses:
            bottom_name = min(scored, key=lambda item: item[1])[0]
            weaknesses = [labels[bottom_name]]

        return strengths[:3], weaknesses[:3]

    @staticmethod
    def _clamp_score(value: int) -> int:
        return max(0, min(100, value))
