from __future__ import annotations

import pytest

from backend.app.services.ai.prompt_builder import PromptBuilder


def test_build_system_prompt_with_sorted_context() -> None:
    builder = PromptBuilder()

    prompt = builder.build_system_prompt(
        base_instruction="Follow policy.",
        context={"zeta": "last", "alpha": "first"},
    )

    assert prompt == "Follow policy.\n\nContext:\n- alpha: first\n- zeta: last"


def test_build_user_prompt_without_context() -> None:
    builder = PromptBuilder()

    prompt = builder.build_user_prompt(user_input="Summarize transactions.")

    assert prompt == "Summarize transactions."


def test_build_prompt_raises_for_empty_content() -> None:
    builder = PromptBuilder()

    with pytest.raises(ValueError, match="cannot be empty"):
        builder.build_user_prompt(user_input="   ")
