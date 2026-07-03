"""High-level AI application service for orchestration and prompt generation."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

from backend.app.services.ai.gemini_client import GeminiClient
from backend.app.services.ai.models import AIHealthStatus, AIResponse
from backend.app.services.ai.prompt_builder import PromptBuilder


class AIService:
    """Coordinate prompt construction and AI provider calls."""

    def __init__(
        self,
        *,
        gemini_client: GeminiClient | None = None,
        prompt_builder: PromptBuilder | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """Create an AI service with injectable dependencies for testability."""

        self._gemini_client = gemini_client or GeminiClient()
        self._prompt_builder = prompt_builder or PromptBuilder()
        self._logger = logger or logging.getLogger(__name__)

    def generate(
        self,
        *,
        system_instruction: str,
        user_input: str,
        system_context: Mapping[str, Any] | None = None,
        user_context: Mapping[str, Any] | None = None,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
    ) -> AIResponse:
        """Generate an AI response from business-layer inputs."""

        system_prompt = self._prompt_builder.build_system_prompt(
            base_instruction=system_instruction,
            context=system_context,
        )
        user_prompt = self._prompt_builder.build_user_prompt(
            user_input=user_input,
            context=user_context,
        )

        request = self._gemini_client.build_request(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )

        self._logger.info("Submitting AI generation request.")
        response = self._gemini_client.generate(request)
        self._logger.info("AI generation completed successfully.")
        return response

    def health(self) -> AIHealthStatus:
        """Return AI configuration health without making external provider calls."""

        configured, model = self._gemini_client.get_configuration_status()
        status = "healthy" if configured else "unhealthy"
        return AIHealthStatus(configured=configured, model=model, status=status)
