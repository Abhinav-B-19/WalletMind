from __future__ import annotations

import pytest
from pydantic import ValidationError

from backend.app.core.config import AppSettings


def test_app_settings_valid_explicit_values() -> None:
    settings = AppSettings(
        _env_file=None,
        gemini_api_key="key-123",
        gemini_model="gemini-2.0-flash",
        temperature=0.6,
        max_output_tokens=2048,
    )

    assert settings.gemini_api_key == "key-123"
    assert settings.gemini_model == "gemini-2.0-flash"
    assert settings.temperature == 0.6
    assert settings.max_output_tokens == 2048


def test_app_settings_missing_api_key() -> None:
    with pytest.raises(ValidationError):
        AppSettings(
            _env_file=None,
            gemini_api_key="",
        )


def test_app_settings_invalid_types() -> None:
    with pytest.raises(ValidationError):
        AppSettings(
            _env_file=None,
            gemini_api_key="key-123",
            temperature="not-a-float",
        )


def test_app_settings_invalid_ranges() -> None:
    with pytest.raises(ValidationError):
        AppSettings(
            _env_file=None,
            gemini_api_key="key-123",
            temperature=3.5,
        )
