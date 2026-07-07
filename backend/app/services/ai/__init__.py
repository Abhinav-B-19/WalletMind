"""Reusable AI service infrastructure for WalletMind."""

from backend.app.services.ai.api_key_provider import (
    clear_request_session,
    delete_session_gemini_key,
    get_active_gemini_key,
    get_gemini_key_status,
    store_session_gemini_key,
)
from backend.app.services.ai.ai_service import AIService
from backend.app.services.ai.exceptions import (
    AIConfigurationError,
    AIRateLimitError,
    AIResponseError,
    AISessionExpiredError,
    AIServiceError,
    AIUserKeyInvalidError,
    AIUserKeyInvalidFormatError,
    AIUserKeyNetworkError,
    AIUserKeyPermissionDeniedError,
    AIUserKeyQuotaExceededError,
    AIUserKeySDKCompatibilityError,
    AIUserKeyUnsupportedAuthKeyError,
    AIUserKeyUnknownError,
)
from backend.app.services.ai.gemini_client import GeminiClient
from backend.app.services.ai.models import AIHealthStatus, AIRequest, AIResponse
from backend.app.services.ai.prompt_builder import PromptBuilder
from backend.app.services.ai.structured_output import parse_json_response

__all__ = [
    "AIConfigurationError",
    "AIHealthStatus",
    "AIRateLimitError",
    "AIRequest",
    "AIResponse",
    "AIResponseError",
    "AISessionExpiredError",
    "AIService",
    "AIServiceError",
    "AIUserKeyInvalidError",
    "AIUserKeyInvalidFormatError",
    "AIUserKeyNetworkError",
    "AIUserKeyPermissionDeniedError",
    "AIUserKeyQuotaExceededError",
    "AIUserKeySDKCompatibilityError",
    "AIUserKeyUnsupportedAuthKeyError",
    "AIUserKeyUnknownError",
    "GeminiClient",
    "clear_request_session",
    "delete_session_gemini_key",
    "get_active_gemini_key",
    "get_gemini_key_status",
    "parse_json_response",
    "PromptBuilder",
    "store_session_gemini_key",
]
