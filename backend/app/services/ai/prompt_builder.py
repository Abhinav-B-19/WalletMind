"""Reusable prompt construction helpers for AI-driven features."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class PromptBuilder:
    """Build canonical system and user prompts from structured inputs."""

    def build_system_prompt(
        self,
        base_instruction: str,
        context: Mapping[str, Any] | None = None,
    ) -> str:
        """Construct a normalized system prompt with optional key/value context."""

        return self._build_prompt(base_instruction=base_instruction, context=context)

    def build_user_prompt(
        self,
        user_input: str,
        context: Mapping[str, Any] | None = None,
    ) -> str:
        """Construct a normalized user prompt with optional key/value context."""

        return self._build_prompt(base_instruction=user_input, context=context)

    @staticmethod
    def _build_prompt(
        base_instruction: str,
        context: Mapping[str, Any] | None,
    ) -> str:
        """Compose prompt text while preserving deterministic context ordering."""

        cleaned_instruction = base_instruction.strip()
        if not cleaned_instruction:
            raise ValueError("Prompt content cannot be empty.")

        if not context:
            return cleaned_instruction

        context_lines = [f"- {key}: {context[key]}" for key in sorted(context)]
        return f"{cleaned_instruction}\n\nContext:\n" + "\n".join(context_lines)
