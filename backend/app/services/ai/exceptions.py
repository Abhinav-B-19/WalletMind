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
