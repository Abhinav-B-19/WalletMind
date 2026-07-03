"""Prioritization engine for deterministic budget recommendations."""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field

from backend.app.services.health.health_score_calculator import HealthScoreComputation


class PriorityRecommendation(BaseModel):
    """Priority recommendation item returned in budget output."""

    title: str = Field(..., min_length=1)
    priority: str = Field(..., pattern="^(low|medium|high)$")
    category: str = Field(..., min_length=1)
    estimated_monthly_saving: float = Field(..., ge=0.0)


class RecommendationPrioritizer:
    """Rank opportunities based on impact, behavior, and financial health."""

    def prioritize(
        self,
        *,
        categories: list[dict[str, object]],
        health: HealthScoreComputation,
    ) -> list[PriorityRecommendation]:
        """Produce deterministic ordered recommendations."""

        health_modifier = self._health_modifier(health)
        scored: list[tuple[Decimal, PriorityRecommendation]] = []

        for item in categories:
            category = str(item.get("category", "Other"))
            potential = Decimal(str(item.get("potential_saving", 0)))
            utilization = Decimal(str(item.get("utilization_ratio", 0)))

            if potential <= 0:
                continue

            impact_score = potential
            behavior_score = utilization * Decimal("120")
            category_weight = self._category_weight(category)
            composite = (
                impact_score * Decimal("0.6")
                + behavior_score * Decimal("0.25")
                + category_weight * Decimal("15")
            ) * health_modifier

            priority = self._priority_from_saving(potential)
            recommendation = PriorityRecommendation(
                title=self._build_title(category=category, potential=potential),
                priority=priority,
                category=category,
                estimated_monthly_saving=float(potential),
            )
            scored.append((composite, recommendation))

        scored.sort(
            key=lambda item: (
                item[0],
                item[1].estimated_monthly_saving,
            ),
            reverse=True,
        )

        return [rec for _, rec in scored[:5]]

    @staticmethod
    def _priority_from_saving(potential: Decimal) -> str:
        if potential >= Decimal("1500"):
            return "high"
        if potential >= Decimal("600"):
            return "medium"
        return "low"

    @staticmethod
    def _build_title(*, category: str, potential: Decimal) -> str:
        return (
            f"Reduce {category} spending by {float(potential):.2f} per month "
            "to improve savings capacity."
        )

    @staticmethod
    def _health_modifier(health: HealthScoreComputation) -> Decimal:
        if health.overall_score < 40:
            return Decimal("1.20")
        if health.overall_score < 60:
            return Decimal("1.10")
        if health.overall_score < 75:
            return Decimal("1.00")
        return Decimal("0.95")

    @staticmethod
    def _category_weight(category: str) -> Decimal:
        normalized = category.strip().lower()
        high_impact = {
            "rent",
            "housing",
            "food & dining",
            "food",
            "transport",
            "utilities",
            "shopping",
        }
        medium_impact = {"entertainment", "travel", "fuel"}
        if normalized in high_impact:
            return Decimal("1.00")
        if normalized in medium_impact:
            return Decimal("0.75")
        return Decimal("0.50")
