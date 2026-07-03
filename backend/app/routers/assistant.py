"""Conversational assistant API endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from backend.app.api.dependencies import get_financial_assistant_service
from backend.app.api.schemas import ErrorResponse
from backend.app.schemas.response import ApiResponse
from backend.app.services.assistant.financial_assistant_service import (
    AssistantChatRequest,
    AssistantChatResponse,
    FinancialAssistantService,
)

router = APIRouter(prefix="/assistant", tags=["assistant"])

error_responses = {
    404: {"model": ErrorResponse, "description": "No relevant data found"},
    422: {"model": ErrorResponse, "description": "Validation error"},
    429: {"model": ErrorResponse, "description": "Rate limit"},
    502: {"model": ErrorResponse, "description": "Invalid AI response"},
    504: {"model": ErrorResponse, "description": "AI timeout"},
}


@router.post(
    "/chat",
    response_model=ApiResponse[AssistantChatResponse],
    status_code=status.HTTP_200_OK,
    responses=error_responses,
)
def assistant_chat(
    payload: AssistantChatRequest,
    service: Annotated[
        FinancialAssistantService,
        Depends(get_financial_assistant_service),
    ],
) -> ApiResponse[AssistantChatResponse]:
    """Answer user financial questions using retrieval-grounded assistant workflow."""

    result = service.chat(payload)
    return ApiResponse(
        message="Assistant response generated successfully.",
        data=result,
    )
