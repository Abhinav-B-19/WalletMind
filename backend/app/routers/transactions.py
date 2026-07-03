"""Transaction retrieval API endpoints."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from backend.app.api.dependencies import get_transaction_service
from backend.app.api.schemas import ErrorResponse
from backend.app.schemas.response import ApiResponse
from walletmind.schemas.transaction import TransactionDTO
from walletmind.services.transaction_service import TransactionService

router = APIRouter(prefix="/transactions", tags=["transactions"])

error_responses = {
    400: {"model": ErrorResponse, "description": "Invalid request"},
    404: {"model": ErrorResponse, "description": "Resource not found"},
    422: {"model": ErrorResponse, "description": "Validation error"},
    500: {"model": ErrorResponse, "description": "Server error"},
}


@router.get(
    "",
    response_model=ApiResponse[list[TransactionDTO]],
    status_code=status.HTTP_200_OK,
    responses=error_responses,
)
def list_transactions(
    statement_uuid: UUID | None = Query(default=None),
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    min_amount: Decimal | None = Query(default=None),
    max_amount: Decimal | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    service: TransactionService = Depends(get_transaction_service),
) -> ApiResponse[list[TransactionDTO]]:
    """List transactions with optional filters and pagination."""

    rows = service.list_transactions(
        statement_uuid=statement_uuid,
        from_date=from_date,
        to_date=to_date,
        min_amount=min_amount,
        max_amount=max_amount,
        page=page,
        page_size=page_size,
    )
    return ApiResponse(message="Transactions retrieved successfully.", data=rows)
