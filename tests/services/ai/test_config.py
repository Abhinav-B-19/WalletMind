from __future__ import annotations

import pytest

from backend.app.core.config import SettingsLoadError, get_ai_settings


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> None:
    get_ai_settings.cache_clear()


def test_get_ai_settings_valid(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "key-123")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-2.0-flash")
    monkeypatch.setenv("TEMPERATURE", "0.6")
    monkeypatch.setenv("MAX_OUTPUT_TOKENS", "2048")

    settings = get_ai_settings()

    assert settings.gemini_api_key == "key-123"
    assert settings.gemini_model == "gemini-2.0-flash"
    assert settings.temperature == 0.6
    assert settings.max_output_tokens == 2048


def test_get_ai_settings_missing_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "")

    with pytest.raises(SettingsLoadError, match="Invalid or missing Gemini"):
        get_ai_settings()


def test_get_ai_settings_invalid_types(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "key-123")
    monkeypatch.setenv("TEMPERATURE", "not-a-float")

    with pytest.raises(SettingsLoadError, match="Invalid or missing Gemini"):
        get_ai_settings()


def test_get_ai_settings_invalid_ranges(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "key-123")
    monkeypatch.setenv("TEMPERATURE", "3.5")

    with pytest.raises(SettingsLoadError, match="Invalid or missing Gemini"):
        get_ai_settings()
