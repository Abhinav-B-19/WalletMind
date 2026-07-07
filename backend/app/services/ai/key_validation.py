"""Provider-based API key validation for AI runtimes.

Current sprint scope includes only Google AI Studio / Gemini Developer API.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol


class APIKeyValidatorProvider(Protocol):
    """Contract for provider-specific API key validation."""

    provider_name: str

    def validate(self, api_key: str) -> None:
        """Validate key by performing a lightweight provider call."""


@dataclass
class GoogleAIStudioKeyValidatorProvider:
    """Google AI Studio / Gemini Developer API key validator."""

    provider_name: str = "google_ai_studio"
    logger: logging.Logger | None = None

    def validate(self, api_key: str) -> None:
        from backend.app.services.ai.gemini_client import GeminiClient

        active_logger = self.logger or logging.getLogger(__name__)
        active_logger.info("gemini_key_validation_sdk_initialized")
        client = GeminiClient(api_key=api_key)

        active_logger.info("gemini_key_validation_request_sent")
        client.validate_api_key_lightweight()

        active_logger.info("gemini_key_validation_google_response")


def get_default_key_validator_provider() -> APIKeyValidatorProvider:
    """Return the active key validator provider for current sprint scope."""

    return GoogleAIStudioKeyValidatorProvider()
