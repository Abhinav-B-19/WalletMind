from __future__ import annotations

from backend.app.services.ai.key_validation import (
    GoogleAIStudioKeyValidatorProvider,
    get_default_key_validator_provider,
)


def test_default_provider_is_google_ai_studio() -> None:
    provider = get_default_key_validator_provider()
    assert provider.provider_name == "google_ai_studio"


def test_google_provider_calls_lightweight_validation(monkeypatch) -> None:
    calls = {"count": 0, "key": None}

    class FakeClient:
        def __init__(self, *, api_key: str) -> None:
            calls["key"] = api_key

        def validate_api_key_lightweight(self) -> None:
            calls["count"] += 1

    monkeypatch.setattr(
        "backend.app.services.ai.gemini_client.GeminiClient",
        FakeClient,
    )

    provider = GoogleAIStudioKeyValidatorProvider()
    provider.validate("AIza-provider-test-key")

    assert calls["key"] == "AIza-provider-test-key"
    assert calls["count"] == 1
