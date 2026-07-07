"""AI infrastructure API endpoints."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.app.api.dependencies import get_ai_service
from backend.app.schemas.response import ApiResponse
from backend.app.services.ai.api_key_provider import (
    delete_session_gemini_key,
    get_gemini_key_status,
    get_session_gemini_key_for_owner,
    store_session_gemini_key,
)
from backend.app.services.ai.ai_service import AIService
from backend.app.services.ai.models import AIHealthStatus

router = APIRouter(prefix="/ai", tags=["ai"])
logger = logging.getLogger(__name__)


class GeminiApiKeyRequest(BaseModel):
    """Request payload for setting a user-managed Gemini API key."""

    api_key: str = Field(..., min_length=1)


class GeminiApiKeyStatusResponse(BaseModel):
    """Safe status envelope that never returns key material."""

    configured: bool
    masked_key: str | None = None
    source: str
    model: str
    last_validated: str | None = None


class GeminiApiKeyRevealResponse(BaseModel):
    """Explicit owner-only key reveal response for eye-toggle interactions."""

    configured: bool
    source: str
    api_key: str


class SuccessResponse(BaseModel):
    """Minimal success response for mutation-style endpoints."""

    success: bool = True


@router.get(
    "/health",
    response_model=ApiResponse[AIHealthStatus],
    status_code=status.HTTP_200_OK,
)
def get_ai_health(
    service: Annotated[AIService, Depends(get_ai_service)],
) -> ApiResponse[AIHealthStatus]:
    """Return AI configuration health without making external provider calls."""

    health = service.health()
    return ApiResponse(message="AI service health retrieved successfully.", data=health)


@router.post(
    "/api-key",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
)
def set_api_key(payload: GeminiApiKeyRequest) -> SuccessResponse:
    """Validate and store the Gemini API key in server-side session memory."""

    logger.info("gemini_key_api_request_received")
    store_session_gemini_key(api_key=payload.api_key)
    logger.info("gemini_key_api_request_succeeded")
    return SuccessResponse(success=True)


@router.get(
    "/api-key/status",
    response_model=GeminiApiKeyStatusResponse,
    status_code=status.HTTP_200_OK,
)
def get_api_key_status() -> GeminiApiKeyStatusResponse:
    """Return non-sensitive Gemini key status for the current session."""

    logger.info("gemini_key_status_request_received")
    status_payload = get_gemini_key_status()
    logger.info(
        "gemini_key_status_request_succeeded",
        extra={"configured": status_payload.get("configured", False)},
    )
    return GeminiApiKeyStatusResponse(**status_payload)


@router.get(
    "/api-key",
    response_model=GeminiApiKeyRevealResponse,
    status_code=status.HTTP_200_OK,
)
def get_api_key_for_owner() -> GeminiApiKeyRevealResponse:
    """Return full session key only for explicit owner reveal workflows."""

    logger.info("gemini_key_reveal_request_received")
    api_key = get_session_gemini_key_for_owner()
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No session Gemini API key is configured.",
        )

    logger.info("gemini_key_reveal_request_succeeded")
    return GeminiApiKeyRevealResponse(
        configured=True,
        source="session",
        api_key=api_key,
    )


@router.delete(
    "/api-key",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
)
def delete_api_key() -> SuccessResponse:
    """Delete the session-scoped Gemini API key."""

    logger.info("gemini_key_delete_request_received")
    delete_session_gemini_key()
    logger.info("gemini_key_delete_request_succeeded")
    return SuccessResponse(success=True)
