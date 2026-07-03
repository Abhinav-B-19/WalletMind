from __future__ import annotations

from backend.app.services.ai.models import AIResponse
from backend.app.services.report.executive_summary_builder import (
    ExecutiveSummaryBuilder,
)


class StubAIService:
    def __init__(self, response: AIResponse) -> None:
        self._response = response
        self.calls = 0
        self.last_kwargs: dict[str, object] | None = None

    def generate(self, **kwargs):
        self.calls += 1
        self.last_kwargs = kwargs
        return self._response


def test_executive_summary_builder_generates_structured_response() -> None:
    ai_service = StubAIService(
        AIResponse(
            text=(
                '{"executive_summary":"Stable month with improving savings behavior.",'
                '"strengths":["Healthy savings rate"],'
                '"risks":["Food spending trend"],'
                '"action_plan":['
                '"Set weekly food cap",'
                '"Review subscriptions",'
                '"Auto-transfer savings"]}'
            ),
            model="gemini-2.5-flash",
            prompt_tokens=120,
            completion_tokens=90,
            total_tokens=210,
            finish_reason="stop",
        )
    )

    builder = ExecutiveSummaryBuilder(ai_service=ai_service)
    result = builder.generate(
        deterministic_sections={
            "health_score": {
                "overall_score": 75,
                "grade": "Good",
                "components": {
                    "savings_rate": 80,
                },
            },
            "budget_recommendations": {
                "overall_potential_savings": 2000,
                "emergency_fund_recommendation": 10000,
                "overspending_categories": ["Food"],
                "priority_recommendations": [],
            },
            "spending_insights": {
                "top_spending_categories": [],
                "top_merchants": [],
                "subscriptions": [],
            },
            "cash_flow": {
                "net_cash_flow": 3000,
                "savings_rate": 30,
                "monthly_averages": {},
            },
        }
    )

    assert result.executive_summary.startswith("Stable month")
    assert result.action_plan == [
        "Set weekly food cap",
        "Review subscriptions",
        "Auto-transfer savings",
    ]
    assert result.prompt_tokens == 120
    assert ai_service.calls == 1
    assert ai_service.last_kwargs is not None
    assert ai_service.last_kwargs["response_mime_type"] == "application/json"
