"""AI infrastructure API endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from backend.app.api.dependencies import get_ai_service
from backend.app.schemas.response import ApiResponse
from backend.app.services.ai.ai_service import AIService
from backend.app.services.ai.models import AIHealthStatus

router = APIRouter(prefix="/ai", tags=["ai"])


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
