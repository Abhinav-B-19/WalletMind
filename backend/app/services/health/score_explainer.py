"""Prompt and response handling for financial health score AI explanations."""

from __future__ import annotations

import json
import re

from pydantic import BaseModel, Field, ValidationError

from backend.app.services.ai.exceptions import AIResponseError
from backend.app.services.health.health_score_calculator import HealthScoreComputation


class ScoreExplanationPayload(BaseModel):
    """Validated AI explanation payload for deterministic health scores."""

    explanation: str = Field(..., min_length=1)
    recommendations: list[str] = Field(default_factory=list)


class ScoreExplainer:
    """Build score explanation prompts and parse AI responses."""

    _SYSTEM_INSTRUCTION = (
        "You are WalletMind Financial Health Coach. "
        "Use only deterministic score and metric data provided. "
        "Never invent numbers. "
        "Never change scores. "
        "Respond as JSON with keys: explanation, recommendations."
    )

    @property
    def system_instruction(self) -> str:
        return self._SYSTEM_INSTRUCTION

    def build_user_prompt(self, *, computation: HealthScoreComputation) -> str:
        """Build structured prompt payload from deterministic score output."""

        payload = {
            "overall_score": computation.overall_score,
            "grade": computation.grade,
            "components": computation.components.model_dump(),
            "metrics": computation.metrics,
            "strengths": computation.strengths,
            "weaknesses": computation.weaknesses,
        }
        return (
            "Explain the financial health score in clear language. "
            "Call out strongest and weakest contributors and suggest practical "
            "improvements tailored to weaknesses. "
            "Do not provide formulas. "
            "Return JSON only.\n"
            f"DATA:\n{json.dumps(payload, ensure_ascii=True, sort_keys=True)}"
        )

    def parse_ai_response(self, raw_text: str) -> ScoreExplanationPayload:
        """Parse and validate AI JSON explanation payload."""

        candidate = raw_text.strip()
        if not candidate:
            raise AIResponseError("AI explanation response was empty.")

        match = re.search(r"```json\s*(\{.*?\})\s*```", candidate, re.DOTALL)
        if match:
            candidate = match.group(1)

        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError as exc:
            raise AIResponseError("AI explanation response is not valid JSON.") from exc

        try:
            return ScoreExplanationPayload.model_validate(parsed)
        except ValidationError as exc:
            raise AIResponseError("AI explanation response schema is invalid.") from exc
