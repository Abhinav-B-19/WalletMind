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


class UnsupportedJsonModeThenSuccessModelsAPI:
    def __init__(self, response: Any) -> None:
        self._response = response
        self.calls = 0
        self.configs: list[dict[str, Any]] = []
        self.last_model: str | None = None
        self.last_contents: str | None = None

    def generate_content(self, *, model: str, contents: str, config: dict[str, Any]) -> Any:
        self.calls += 1
        self.last_model = model
        self.last_contents = contents
        self.configs.append(config)
        if self.calls == 1:
            raise TypeError("Unknown field: response_schema")
        return self._response

    def list(self, *, config: dict[str, Any]) -> Any:  # noqa: ARG002
        return iter([SimpleNamespace(name="gemini-2.5-flash")])


class FakeModelsAPI:
    def __init__(
        self,
        *,
        response: Any = None,
        generate_error: Exception | None = None,
        list_error: Exception | None = None,
        list_items: list[Any] | None = None,
    ) -> None:
        self._response = response
        self._generate_error = generate_error
        self._list_error = list_error
        self._list_items = list_items if list_items is not None else [SimpleNamespace(name="gemini-2.5-flash")]
        self.last_generate_model: str | None = None
        self.last_generate_contents: str | None = None
        self.last_generate_config: dict[str, Any] | None = None
        self.last_list_config: dict[str, Any] | None = None

    def generate_content(self, *, model: str, contents: str, config: dict[str, Any]) -> Any:
        self.last_generate_model = model
        self.last_generate_contents = contents
        self.last_generate_config = config
        if self._generate_error is not None:
            raise self._generate_error
        return self._response

    def list(self, *, config: dict[str, Any]) -> Any:
        self.last_list_config = config
        if self._list_error is not None:
            raise self._list_error
        return iter(self._list_items)


class FakeSDKClient:
    def __init__(self, models: Any) -> None:
        self.models = models


class FakeSDKModule:
    def __init__(self, sdk_client: FakeSDKClient) -> None:
        self._sdk_client = sdk_client
        self.created_api_keys: list[str] = []

    def Client(self, *, api_key: str) -> FakeSDKClient:  # noqa: N802
        self.created_api_keys.append(api_key)
        return self._sdk_client


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
    candidate = SimpleNamespace(finish_reason=SimpleNamespace(name="STOP"))
    return SimpleNamespace(
        text="Generated answer",
        usage_metadata=usage_metadata,
        candidates=[candidate],
    )


def test_gemini_client_initializes_lazily() -> None:
    load_calls = {"count": 0}
    models = FakeModelsAPI(response=_make_success_response())
    sdk_module = FakeSDKModule(sdk_client=FakeSDKClient(models=models))

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
    assert sdk_module.created_api_keys == ["env-key"]
    assert models.last_generate_model == "gemini-2.5-flash"
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
    models = FakeModelsAPI(generate_error=TimeoutError("timeout"))
    sdk_module = FakeSDKModule(sdk_client=FakeSDKClient(models=models))
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
    models = FakeModelsAPI(generate_error=RuntimeError("rate limit exceeded"))
    sdk_module = FakeSDKModule(sdk_client=FakeSDKClient(models=models))
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
    models = FakeModelsAPI(response=SimpleNamespace(text="   ", candidates=[]))
    sdk_module = FakeSDKModule(sdk_client=FakeSDKClient(models=models))
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
    models = FakeModelsAPI(response=_make_success_response())
    sdk_module = FakeSDKModule(sdk_client=FakeSDKClient(models=models))
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

    configured, model, source = client.get_configuration_status()

    assert configured is False
    assert model == "gemini-2.5-flash"
    assert source == "none"


def test_gemini_client_passes_json_mode_generation_config() -> None:
    models = FakeModelsAPI(response=_make_success_response())
    sdk_module = FakeSDKModule(sdk_client=FakeSDKClient(models=models))
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

    assert models.last_generate_config is not None
    assert models.last_generate_config["response_mime_type"] == "application/json"
    assert "response_schema" in models.last_generate_config


def test_gemini_client_generation_config_copies_schema_object() -> None:
    models = FakeModelsAPI(response=_make_success_response())
    sdk_module = FakeSDKModule(sdk_client=FakeSDKClient(models=models))
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

    assert models.last_generate_config is not None
    assert models.last_generate_config["response_schema"] == schema
    assert models.last_generate_config["response_schema"] is not schema


def test_gemini_client_falls_back_when_json_mode_not_supported() -> None:
    models = UnsupportedJsonModeThenSuccessModelsAPI(
        response=_make_success_response()
    )
    sdk_module = FakeSDKModule(sdk_client=FakeSDKClient(models=models))
    client = GeminiClient(api_key="k", sdk_loader=lambda: sdk_module)

    request = client.build_request(
        system_prompt="system",
        user_prompt="user",
        response_mime_type="application/json",
        response_schema={"type": "object"},
    )
    response = client.generate(request)

    assert response.text == "Generated answer"
    assert models.calls == 2
    assert "response_schema" in models.configs[0]
    assert "response_schema" not in models.configs[1]


def test_validate_api_key_lightweight_uses_list_models() -> None:
    models = FakeModelsAPI(response=_make_success_response())
    sdk_module = FakeSDKModule(sdk_client=FakeSDKClient(models=models))
    client = GeminiClient(api_key="AQ-test-key", sdk_loader=lambda: sdk_module)

    client.validate_api_key_lightweight()

    assert sdk_module.created_api_keys == ["AQ-test-key"]
    assert models.last_list_config == {"page_size": 1}
