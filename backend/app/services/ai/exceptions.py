"""Custom exceptions for AI infrastructure services."""

from __future__ import annotations


class AIServiceError(Exception):
    """Base error for AI service operations."""


class AIConfigurationError(AIServiceError):
    """Raised when AI configuration is missing or invalid."""


class AIRateLimitError(AIServiceError):
    """Raised when the upstream AI provider enforces a rate limit."""


class AIResponseError(AIServiceError):
    """Raised when the AI provider returns an invalid or empty response."""


class AIUserKeyInvalidError(AIConfigurationError):
    """Raised when a user-supplied Gemini key cannot be validated."""


class AIUserKeyInvalidFormatError(AIUserKeyInvalidError):
    """Raised when submitted credential is not an AI Studio Gemini API key."""


class AIUserKeyNetworkError(AIUserKeyInvalidError):
    """Raised when key validation fails due to network connectivity issues."""


class AIUserKeyQuotaExceededError(AIUserKeyInvalidError):
    """Raised when key validation fails because provider quota is exceeded."""


class AIUserKeyPermissionDeniedError(AIUserKeyInvalidError):
    """Raised when key validation fails due to permission or access errors."""


class AIUserKeyUnsupportedAuthKeyError(AIUserKeyInvalidError):
    """Raised when SDK/provider cannot process the submitted auth key type."""


class AIUserKeySDKCompatibilityError(AIUserKeyInvalidError):
    """Raised when local SDK is incompatible with current key validation flow."""


class AIUserKeyUnknownError(AIUserKeyInvalidError):
    """Raised when key validation fails for an uncategorized upstream reason."""


class AISessionExpiredError(AIConfigurationError):
    """Raised when the request session no longer has an active key."""
