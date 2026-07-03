"""Gemini SDK client wrapper for resilient AI inference calls."""

from __future__ import annotations

import copy
import logging
from collections.abc import Callable
from typing import Any

from pydantic import ValidationError

from backend.app.core.config import AISettings, SettingsLoadError, get_ai_settings
from backend.app.services.ai.exceptions import (
    AIConfigurationError,
    AIRateLimitError,
    AIResponseError,
    AIServiceError,
)
from backend.app.services.ai.models import AIRequest, AIResponse


class GeminiClient:
    """Thin client around Google Gemini with config validation and error mapping."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
        sdk_loader: Callable[[], Any] | None = None,
        settings_provider: Callable[[], AISettings] | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize the client with optional explicit configuration overrides."""

        self._api_key = api_key
        self._model = model
        self._temperature = temperature
        self._max_output_tokens = max_output_tokens
        self._sdk_loader = sdk_loader or self._default_sdk_loader
        self._settings_provider = settings_provider or get_ai_settings
        self._sdk_module: Any | None = None
        self._model_client: Any | None = None
        self._logger = logger or logging.getLogger(__name__)

    def generate(self, request: AIRequest) -> AIResponse:
        """Generate a text completion using Gemini for the provided request."""

        self._validate_request(request)
        sdk = self._get_sdk_module()
        model_client = self._get_model_client(sdk)

        generation_config = self._build_generation_config(request=request)
        prompt = self._compose_prompt(request=request)

        try:
            raw_response = self._generate_content(
                model_client=model_client,
                prompt=prompt,
                generation_config=generation_config,
                request=request,
            )
        except TimeoutError as exc:
            raise AIServiceError("Gemini request timed out.") from exc
        except Exception as exc:  # pragma: no cover - defensive provider mapping
            if "rate" in str(exc).lower() and "limit" in str(exc).lower():
                raise AIRateLimitError("Gemini rate limit exceeded.") from exc
            self._logger.exception("Gemini request failed")
            raise AIServiceError(
                f"Gemini request failed: {type(exc).__name__}: {exc}"
            ) from exc

        return self._parse_response(raw_response)

    def get_configuration_status(self) -> tuple[bool, str]:
        """Return a lightweight health snapshot without calling the external API."""

        try:
            self._resolve_api_key()
            model = self._resolve_model()
            self._resolve_temperature()
            self._resolve_max_output_tokens()
        except AIConfigurationError:
            return False, self._fallback_model_name()
        return True, model

    def build_request(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
        response_mime_type: str | None = None,
        response_schema: dict[str, Any] | None = None,
    ) -> AIRequest:
        """Build a validated AI request using defaults when values are omitted."""

        request_temperature = (
            temperature if temperature is not None else self._resolve_temperature()
        )
        request_max_tokens = (
            max_output_tokens
            if max_output_tokens is not None
            else self._resolve_max_output_tokens()
        )

        try:
            return AIRequest(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=request_temperature,
                max_output_tokens=request_max_tokens,
                response_mime_type=response_mime_type,
                response_schema=response_schema,
            )
        except ValidationError as exc:
            raise AIConfigurationError("Invalid AI request values.") from exc

    def _build_generation_config(self, *, request: AIRequest) -> dict[str, Any]:
        config: dict[str, Any] = {
            "temperature": request.temperature,
            "max_output_tokens": request.max_output_tokens,
        }
        if request.response_mime_type is not None:
            config["response_mime_type"] = request.response_mime_type
        if request.response_schema is not None:
            config["response_schema"] = copy.deepcopy(request.response_schema)
        return config

    def _generate_content(
        self,
        *,
        model_client: Any,
        prompt: str,
        generation_config: dict[str, Any],
        request: AIRequest,
    ) -> Any:
        try:
            return model_client.generate_content(
                prompt,
                generation_config=generation_config,
            )
        except Exception as exc:
            if self._is_json_mode_unsupported_error(exc=exc, request=request):
                self._logger.warning(
                    "Gemini SDK does not support response_mime_type/response_schema; "
                    "falling back to prompt-only JSON enforcement."
                )
                fallback_config = {
                    "temperature": request.temperature,
                    "max_output_tokens": request.max_output_tokens,
                }
                return model_client.generate_content(
                    prompt,
                    generation_config=fallback_config,
                )
            raise

    @staticmethod
    def _is_json_mode_unsupported_error(*, exc: Exception, request: AIRequest) -> bool:
        if request.response_mime_type is None and request.response_schema is None:
            return False

        message = str(exc).lower()
        return (
            "response_mime_type" in message
            or "response_schema" in message
            or "unknown field" in message
            or "unexpected keyword" in message
            or "invalid generation config" in message
        )

    def _get_sdk_module(self) -> Any:
        if self._sdk_module is None:
            self._resolve_api_key()
            self._sdk_module = self._sdk_loader()
            self._sdk_module.configure(api_key=self._resolve_api_key())
        return self._sdk_module

    def _get_model_client(self, sdk_module: Any) -> Any:
        if self._model_client is None:
            self._model_client = sdk_module.GenerativeModel(self._resolve_model())
        return self._model_client

    def _compose_prompt(self, request: AIRequest) -> str:
        """Serialize request prompts into one deterministic provider payload."""

        return (
            "System Prompt:\n"
            f"{request.system_prompt.strip()}\n\n"
            "User Prompt:\n"
            f"{request.user_prompt.strip()}"
        )

    def _parse_response(self, response: Any) -> AIResponse:
        text = (getattr(response, "text", "") or "").strip()
        if not text:
            raise AIResponseError("Gemini returned an empty response.")

        usage = getattr(response, "usage_metadata", None)
        prompt_tokens = int(getattr(usage, "prompt_token_count", 0) or 0)
        completion_tokens = int(getattr(usage, "candidates_token_count", 0) or 0)
        total_tokens = int(getattr(usage, "total_token_count", 0) or 0)

        finish_reason = "unknown"
        candidates = getattr(response, "candidates", None)
        if candidates:
            finish_reason = str(
                getattr(candidates[0], "finish_reason", "unknown")
            ).lower()

        return AIResponse(
            text=text,
            model=self._resolve_model(),
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            finish_reason=finish_reason,
        )

    def _validate_request(self, request: AIRequest) -> None:
        """Validate request payload and configured runtime dependencies."""

        if not request.system_prompt.strip() or not request.user_prompt.strip():
            raise AIResponseError("Request prompts must not be empty.")

        self._resolve_api_key()
        self._resolve_temperature()
        self._resolve_max_output_tokens()

    def _resolve_api_key(self) -> str:
        api_key = (
            self._api_key
            if self._api_key is not None
            else self._settings().gemini_api_key
        )
        api_key = api_key.strip()
        if not api_key:
            raise AIConfigurationError("GEMINI_API_KEY is not configured.")
        return api_key

    def _resolve_model(self) -> str:
        model = (
            self._model if self._model is not None else self._settings().gemini_model
        )
        model = model.strip()
        if not model:
            raise AIConfigurationError("GEMINI_MODEL is invalid.")
        return model

    def _resolve_temperature(self) -> float:
        value: Any = (
            self._temperature
            if self._temperature is not None
            else self._settings().temperature
        )
        try:
            temperature = float(value)
        except (TypeError, ValueError) as exc:
            raise AIConfigurationError("TEMPERATURE must be a valid float.") from exc

        if temperature < 0.0 or temperature > 2.0:
            raise AIConfigurationError("TEMPERATURE must be between 0.0 and 2.0.")
        return temperature

    def _resolve_max_output_tokens(self) -> int:
        value: Any = (
            self._max_output_tokens
            if self._max_output_tokens is not None
            else self._settings().max_output_tokens
        )
        try:
            max_tokens = int(value)
        except (TypeError, ValueError) as exc:
            raise AIConfigurationError(
                "MAX_OUTPUT_TOKENS must be a valid integer."
            ) from exc

        if max_tokens <= 0:
            raise AIConfigurationError("MAX_OUTPUT_TOKENS must be greater than zero.")
        return max_tokens

    def _settings(self) -> AISettings:
        """Retrieve validated AI settings from the single configuration source."""

        try:
            return self._settings_provider()
        except SettingsLoadError as exc:
            raise AIConfigurationError(str(exc)) from exc
        except AIConfigurationError:
            raise
        except Exception as exc:  # pragma: no cover - defensive adapter
            raise AIConfigurationError("Failed to load AI settings.") from exc

    @staticmethod
    def _fallback_model_name() -> str:
        """Return configured default model name from AI settings schema."""

        default_model = AISettings.model_fields["gemini_model"].default
        return str(default_model)

    @staticmethod
    def _default_sdk_loader() -> Any:
        try:
            import google.generativeai as genai
        except ImportError as exc:  # pragma: no cover - import guard depends on env
            raise AIConfigurationError(
                "google-generativeai is not installed. Add it to runtime dependencies."
            ) from exc
        return genai
