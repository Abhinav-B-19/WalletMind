from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from backend.app.services.ai.exceptions import (
    AIConfigurationError,
    AIRateLimitError,
    AIResponseError,
    AIServiceError,
)
from backend.app.services.ai.gemini_client import GeminiClient
from backend.app.services.ai.models import AIRequest


class FakeModelClient:
    def __init__(self, *, response: Any = None, error: Exception | None = None) -> None:
        self._response = response
        self._error = error
        self.last_prompt: str | None = None
        self.last_generation_config: dict[str, Any] | None = None

    def generate_content(self, prompt: str, generation_config: dict[str, Any]) -> Any:
        self.last_prompt = prompt
        self.last_generation_config = generation_config
        if self._error is not None:
            raise self._error
        return self._response


class UnsupportedJsonModeThenSuccessModelClient:
    def __init__(self, response: Any) -> None:
        self._response = response
        self.calls = 0
        self.configs: list[dict[str, Any]] = []

    def generate_content(self, prompt: str, generation_config: dict[str, Any]) -> Any:
        self.calls += 1
        self.configs.append(generation_config)
        if self.calls == 1:
            raise TypeError("Unknown field: response_schema")
        return self._response


class FakeSDKModule:
    def __init__(self, model_client: FakeModelClient) -> None:
        self.model_client = model_client
        self.configure_api_key: str | None = None
        self.model_name: str | None = None

    def configure(self, *, api_key: str) -> None:
        self.configure_api_key = api_key

    def GenerativeModel(self, model_name: str) -> FakeModelClient:  # noqa: N802
        self.model_name = model_name
        return self.model_client


class StubSettings:
    def __init__(
        self,
        *,
        gemini_api_key: str = "stub-key",
        gemini_model: str = "gemini-2.5-flash",
        temperature: float = 0.2,
        max_output_tokens: int = 1024,
    ) -> None:
        self.gemini_api_key = gemini_api_key
        self.gemini_model = gemini_model
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens


def _make_success_response() -> Any:
    usage_metadata = SimpleNamespace(
        prompt_token_count=7,
        candidates_token_count=11,
        total_token_count=18,
    )
    candidate = SimpleNamespace(finish_reason="STOP")
    return SimpleNamespace(
        text="Generated answer",
        usage_metadata=usage_metadata,
        candidates=[candidate],
    )


def test_gemini_client_initializes_lazily() -> None:
    load_calls = {"count": 0}
    sdk_module = FakeSDKModule(
        model_client=FakeModelClient(response=_make_success_response())
    )

    def _loader() -> FakeSDKModule:
        load_calls["count"] += 1
        return sdk_module

    client = GeminiClient(
        sdk_loader=_loader,
        settings_provider=lambda: StubSettings(gemini_api_key="env-key"),
    )

    assert load_calls["count"] == 0

    response = client.generate(
        AIRequest(
            system_prompt="system",
            user_prompt="user",
            temperature=0.2,
            max_output_tokens=120,
        )
    )

    assert load_calls["count"] == 1
    assert sdk_module.configure_api_key == "env-key"
    assert sdk_module.model_name == "gemini-2.5-flash"
    assert response.text == "Generated answer"
    assert response.total_tokens == 18


def test_gemini_client_missing_api_key_raises() -> None:
    client = GeminiClient(api_key="")

    with pytest.raises(AIConfigurationError, match="GEMINI_API_KEY"):
        client.generate(
            AIRequest(
                system_prompt="system",
                user_prompt="user",
                temperature=0.1,
                max_output_tokens=256,
            )
        )


def test_gemini_client_invalid_temperature_raises() -> None:
    client = GeminiClient(api_key="k", temperature=9.0)

    with pytest.raises(AIConfigurationError, match="TEMPERATURE"):
        client.build_request(system_prompt="s", user_prompt="u")


def test_gemini_client_invalid_max_tokens_raises() -> None:
    client = GeminiClient(api_key="k", max_output_tokens=0)

    with pytest.raises(AIConfigurationError, match="MAX_OUTPUT_TOKENS"):
        client.build_request(system_prompt="s", user_prompt="u")


def test_gemini_client_timeout_maps_to_service_error() -> None:
    sdk_module = FakeSDKModule(
        model_client=FakeModelClient(error=TimeoutError("timeout"))
    )
    client = GeminiClient(
        api_key="k",
        sdk_loader=lambda: sdk_module,
    )

    with pytest.raises(AIServiceError, match="timed out"):
        client.generate(
            AIRequest(
                system_prompt="system",
                user_prompt="user",
                temperature=0.2,
                max_output_tokens=128,
            )
        )


def test_gemini_client_rate_limit_maps_to_custom_error() -> None:
    sdk_module = FakeSDKModule(
        model_client=FakeModelClient(error=RuntimeError("rate limit exceeded"))
    )
    client = GeminiClient(
        api_key="k",
        sdk_loader=lambda: sdk_module,
    )

    with pytest.raises(AIRateLimitError, match="rate limit"):
        client.generate(
            AIRequest(
                system_prompt="system",
                user_prompt="user",
                temperature=0.2,
                max_output_tokens=128,
            )
        )


def test_gemini_client_empty_response_raises() -> None:
    sdk_module = FakeSDKModule(
        model_client=FakeModelClient(
            response=SimpleNamespace(text="   ", candidates=[])
        )
    )
    client = GeminiClient(
        api_key="k",
        sdk_loader=lambda: sdk_module,
    )

    with pytest.raises(AIResponseError, match="empty response"):
        client.generate(
            AIRequest(
                system_prompt="system",
                user_prompt="user",
                temperature=0.2,
                max_output_tokens=128,
            )
        )


def test_gemini_client_invalid_request_prompts_raise() -> None:
    sdk_module = FakeSDKModule(
        model_client=FakeModelClient(response=_make_success_response())
    )
    client = GeminiClient(api_key="k", sdk_loader=lambda: sdk_module)

    with pytest.raises(AIResponseError, match="must not be empty"):
        client.generate(
            AIRequest(
                system_prompt="sys",
                user_prompt="user",
                temperature=0.2,
                max_output_tokens=128,
            ).model_copy(update={"system_prompt": "   "})
        )


def test_configuration_status_handles_missing_api_key() -> None:
    client = GeminiClient(api_key="")

    configured, model = client.get_configuration_status()

    assert configured is False
    assert model == "gemini-2.5-flash"


def test_gemini_client_passes_json_mode_generation_config() -> None:
    model_client = FakeModelClient(response=_make_success_response())
    sdk_module = FakeSDKModule(model_client=model_client)
    client = GeminiClient(api_key="k", sdk_loader=lambda: sdk_module)

    request = client.build_request(
        system_prompt="system",
        user_prompt="user",
        response_mime_type="application/json",
        response_schema={
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
            },
        },
    )
    client.generate(request)

    assert model_client.last_generation_config is not None
    assert (
        model_client.last_generation_config["response_mime_type"] == "application/json"
    )
    assert "response_schema" in model_client.last_generation_config


def test_gemini_client_generation_config_copies_schema_object() -> None:
    model_client = FakeModelClient(response=_make_success_response())
    sdk_module = FakeSDKModule(model_client=model_client)
    client = GeminiClient(api_key="k", sdk_loader=lambda: sdk_module)

    schema = {
        "type": "object",
        "properties": {"summary": {"type": "string"}},
    }
    request = client.build_request(
        system_prompt="system",
        user_prompt="user",
        response_mime_type="application/json",
        response_schema=schema,
    )
    client.generate(request)

    assert model_client.last_generation_config is not None
    assert model_client.last_generation_config["response_schema"] == schema
    assert model_client.last_generation_config["response_schema"] is not schema


def test_gemini_client_falls_back_when_json_mode_not_supported() -> None:
    model_client = UnsupportedJsonModeThenSuccessModelClient(
        response=_make_success_response()
    )
    sdk_module = FakeSDKModule(model_client=model_client)
    client = GeminiClient(api_key="k", sdk_loader=lambda: sdk_module)

    request = client.build_request(
        system_prompt="system",
        user_prompt="user",
        response_mime_type="application/json",
        response_schema={"type": "object"},
    )
    response = client.generate(request)

    assert response.text == "Generated answer"
    assert model_client.calls == 2
    assert "response_schema" in model_client.configs[0]
    assert "response_schema" not in model_client.configs[1]
