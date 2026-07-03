"""AI executive summary generation for monthly financial report."""

from __future__ import annotations

import json

from pydantic import BaseModel, Field, ValidationError

from backend.app.services.ai.ai_service import AIService
from backend.app.services.ai.exceptions import AIResponseError


class ExecutiveSummaryResult(BaseModel):
    """Structured AI output used by monthly report service."""

    executive_summary: str = Field(..., min_length=1, max_length=1800)
    strengths: list[str] = Field(default_factory=list, max_length=6)
    risks: list[str] = Field(default_factory=list, max_length=6)
    action_plan: list[str] = Field(..., min_length=3, max_length=3)
    model: str = Field(..., min_length=1)
    prompt_tokens: int = Field(default=0, ge=0)
    completion_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)
    finish_reason: str = Field(default="unknown", min_length=1)


class ExecutiveSummaryBuilder:
    """Prepare compact AI context and parse executive monthly narrative."""

    _RESPONSE_SCHEMA = {
        "type": "object",
        "required": ["executive_summary", "strengths", "risks", "action_plan"],
        "properties": {
            "executive_summary": {"type": "string", "minLength": 1},
            "strengths": {
                "type": "array",
                "items": {"type": "string"},
            },
            "risks": {
                "type": "array",
                "items": {"type": "string"},
            },
            "action_plan": {
                "type": "array",
                "minItems": 3,
                "maxItems": 3,
                "items": {"type": "string"},
            },
        },
        "additionalProperties": False,
    }

    _SYSTEM_INSTRUCTION = (
        "You are WalletMind Monthly Financial Reporter. "
        "Use only deterministic values provided. "
        "Never fabricate values or assumptions. "
        "Do not suggest financial products, investments, loans, or insurance. "
        "Return concise professional narrative in at most 500 words total. "
        "No markdown tables. "
        "Return JSON only with keys: executive_summary, strengths, risks, action_plan. "
        "Action plan must contain exactly 3 practical steps."
    )

    def __init__(self, *, ai_service: AIService) -> None:
        self._ai_service = ai_service

    def build_context(
        self, *, deterministic_sections: dict[str, object]
    ) -> dict[str, object]:
        """Build compact, safe context for executive AI narrative generation."""

        health_score = deterministic_sections["health_score"]
        budget = deterministic_sections["budget_recommendations"]
        spending = deterministic_sections["spending_insights"]
        cash_flow = deterministic_sections["cash_flow"]

        return {
            "health_score": {
                "overall_score": health_score.get("overall_score"),
                "grade": health_score.get("grade"),
                "components": health_score.get("components", {}),
            },
            "budget_recommendations": {
                "overall_potential_savings": budget.get("overall_potential_savings"),
                "emergency_fund_recommendation": budget.get(
                    "emergency_fund_recommendation"
                ),
                "overspending_categories": budget.get("overspending_categories", [])[
                    :5
                ],
                "priority_recommendations": budget.get("priority_recommendations", [])[
                    :3
                ],
            },
            "spending_insights": {
                "top_spending_categories": spending.get("top_spending_categories", [])[
                    :5
                ],
                "top_merchants": spending.get("top_merchants", [])[:5],
                "subscriptions": spending.get("subscriptions", [])[:5],
            },
            "cash_flow": {
                "net_cash_flow": cash_flow.get("net_cash_flow"),
                "savings_rate": cash_flow.get("savings_rate"),
                "monthly_averages": cash_flow.get("monthly_averages", {}),
            },
        }

    def generate(
        self, *, deterministic_sections: dict[str, object]
    ) -> ExecutiveSummaryResult:
        """Generate executive summary and action plan from deterministic sections."""

        context = self.build_context(deterministic_sections=deterministic_sections)
        user_prompt = (
            "Create a concise monthly financial review using only "
            "this deterministic context. "
            "Include positive observations, biggest concerns, and future focus. "
            "Keep total content under 500 words. "
            "Return JSON only with this shape: "
            '{"executive_summary": string, "strengths": string[], '
            '"risks": string[], "action_plan": [string, string, string]}.\n'
            f"DATA:\n{json.dumps(context, ensure_ascii=True, sort_keys=True)}"
        )

        response = self._ai_service.generate(
            system_instruction=self._SYSTEM_INSTRUCTION,
            user_input=user_prompt,
            response_mime_type="application/json",
            response_schema=self._RESPONSE_SCHEMA,
            max_output_tokens=900,
        )
        return self._parse_ai_response(
            raw_text=response.text,
            model=response.model,
            prompt_tokens=response.prompt_tokens,
            completion_tokens=response.completion_tokens,
            total_tokens=response.total_tokens,
            finish_reason=response.finish_reason,
        )

    def _parse_ai_response(
        self,
        *,
        raw_text: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        finish_reason: str,
    ) -> ExecutiveSummaryResult:
        candidate = raw_text.strip()
        if not candidate:
            raise AIResponseError(
                "Monthly report executive summary response was empty."
            )

        if candidate.startswith("```"):
            lines = candidate.splitlines()
            if len(lines) >= 3 and lines[-1].strip() == "```":
                candidate = "\n".join(lines[1:-1]).strip()

        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError as exc:
            raise AIResponseError(
                "Monthly report executive summary response is not valid JSON."
            ) from exc

        payload["model"] = model
        payload["prompt_tokens"] = prompt_tokens
        payload["completion_tokens"] = completion_tokens
        payload["total_tokens"] = total_tokens
        payload["finish_reason"] = finish_reason

        try:
            return ExecutiveSummaryResult.model_validate(payload)
        except ValidationError as exc:
            raise AIResponseError(
                "Monthly report executive summary response schema is invalid."
            ) from exc
