"""Statement upload and metadata management API endpoints."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile, status

from backend.app.api.dependencies import (
    get_budget_service,
    get_financial_health_service,
    get_financial_report_service,
    get_processing_dispatcher,
    get_spending_insights_service,
    get_statement_upload_service,
    get_transaction_service,
)
from backend.app.api.schemas import ErrorResponse
from backend.app.schemas.response import ApiResponse, DeleteStatusData
from backend.app.services.analysis.spending_insights_service import (
    SpendingInsightsResult,
    SpendingInsightsService,
)
from backend.app.services.budget.budget_service import (
    BudgetRecommendationResult,
    BudgetService,
)
from backend.app.services.health.financial_health_service import (
    FinancialHealthScoreResult,
    FinancialHealthService,
)
from backend.app.services.report.financial_report_service import (
    FinancialReportService,
    MonthlyFinancialReportResult,
)
from walletmind.schemas.statement import UploadResponseDTO
from walletmind.schemas.transaction import TransactionDTO
from walletmind.services.processing_dispatcher import ProcessingDispatcher
from walletmind.services.statement_upload_service import StatementUploadService
from walletmind.services.transaction_service import TransactionService

router = APIRouter(prefix="/statements", tags=["statements"])

error_responses = {
    400: {"model": ErrorResponse, "description": "Invalid uploaded file"},
    404: {"model": ErrorResponse, "description": "Resource not found"},
    413: {"model": ErrorResponse, "description": "Uploaded file too large"},
    415: {"model": ErrorResponse, "description": "Unsupported media type"},
    422: {"model": ErrorResponse, "description": "Validation error"},
    500: {"model": ErrorResponse, "description": "Storage failure"},
}


@router.post(
    "/upload",
    response_model=ApiResponse[UploadResponseDTO],
    status_code=status.HTTP_201_CREATED,
    responses=error_responses,
)
async def upload_statement(
    background_tasks: BackgroundTasks,
    user_uuid: Annotated[UUID, Form(...)],
    file: Annotated[UploadFile, File(...)],
    service: Annotated[
        StatementUploadService,
        Depends(get_statement_upload_service),
    ],
    dispatcher: Annotated[
        ProcessingDispatcher,
        Depends(get_processing_dispatcher),
    ],
) -> ApiResponse[UploadResponseDTO]:
    """Upload a statement file and persist metadata."""

    file_bytes = await file.read()
    statement = service.upload_statement(
        user_uuid=user_uuid,
        original_filename=file.filename or "",
        file_bytes=file_bytes,
    )
    dispatcher.dispatch(
        background_tasks=background_tasks,
        statement_uuid=statement.statement_uuid,
        original_filename=statement.original_filename,
        stored_file_path=statement.stored_file_path or "",
        content_type=file.content_type,
    )
    refreshed_statement = service.get_statement(statement.statement_uuid)
    return ApiResponse(
        message="Statement uploaded successfully.",
        data=refreshed_statement,
    )


@router.get(
    "",
    response_model=ApiResponse[list[UploadResponseDTO]],
    status_code=status.HTTP_200_OK,
    responses=error_responses,
)
def list_statements(
    user_uuid: UUID | None = None,
    *,
    service: Annotated[
        StatementUploadService,
        Depends(get_statement_upload_service),
    ],
) -> ApiResponse[list[UploadResponseDTO]]:
    """List all uploaded statement metadata records."""

    statements = service.list_statements(user_uuid=user_uuid)
    return ApiResponse(message="Statements retrieved successfully.", data=statements)


@router.get(
    "/{statement_uuid}",
    response_model=ApiResponse[UploadResponseDTO],
    status_code=status.HTTP_200_OK,
    responses=error_responses,
)
def get_statement(
    statement_uuid: UUID,
    *,
    service: Annotated[
        StatementUploadService,
        Depends(get_statement_upload_service),
    ],
) -> ApiResponse[UploadResponseDTO]:
    """Get metadata for a single uploaded statement."""

    statement = service.get_statement(statement_uuid)
    return ApiResponse(message="Statement retrieved successfully.", data=statement)


@router.delete(
    "/{statement_uuid}",
    response_model=ApiResponse[DeleteStatusData],
    status_code=status.HTTP_200_OK,
    responses=error_responses,
)
def delete_statement(
    statement_uuid: UUID,
    *,
    service: Annotated[
        StatementUploadService,
        Depends(get_statement_upload_service),
    ],
) -> ApiResponse[DeleteStatusData]:
    """Delete statement metadata and the uploaded file."""

    service.delete_statement(statement_uuid)
    return ApiResponse(
        message="Statement deleted successfully.",
        data=DeleteStatusData(statement_uuid=str(statement_uuid)),
    )


@router.get(
    "/{statement_uuid}/transactions",
    response_model=ApiResponse[list[TransactionDTO]],
    status_code=status.HTTP_200_OK,
    responses=error_responses,
)
def get_statement_transactions(
    statement_uuid: UUID,
    *,
    service: Annotated[
        TransactionService,
        Depends(get_transaction_service),
    ],
) -> ApiResponse[list[TransactionDTO]]:
    """List all parsed transactions for a statement."""

    rows = service.get_statement_transactions(statement_uuid=statement_uuid)
    return ApiResponse(
        message="Statement transactions retrieved successfully.",
        data=rows,
    )


@router.get(
    "/{statement_uuid}/insights",
    response_model=ApiResponse[SpendingInsightsResult],
    status_code=status.HTTP_200_OK,
    responses=error_responses,
)
def get_statement_insights(
    statement_uuid: UUID,
    *,
    service: Annotated[
        SpendingInsightsService,
        Depends(get_spending_insights_service),
    ],
) -> ApiResponse[SpendingInsightsResult]:
    """Generate AI spending insights for a processed statement."""

    result = service.generate_statement_insights(statement_uuid=statement_uuid)
    return ApiResponse(
        message="Statement insights generated successfully.",
        data=result,
    )


@router.get(
    "/{statement_uuid}/health-score",
    response_model=ApiResponse[FinancialHealthScoreResult],
    status_code=status.HTTP_200_OK,
    responses=error_responses,
)
def get_statement_health_score(
    statement_uuid: UUID,
    *,
    service: Annotated[
        FinancialHealthService,
        Depends(get_financial_health_service),
    ],
) -> ApiResponse[FinancialHealthScoreResult]:
    """Generate deterministic financial health score with AI explanation."""

    result = service.generate_statement_health_score(statement_uuid=statement_uuid)
    return ApiResponse(
        message="Statement health score generated successfully.",
        data=result,
    )


@router.get(
    "/{statement_uuid}/budget-recommendations",
    response_model=ApiResponse[BudgetRecommendationResult],
    status_code=status.HTTP_200_OK,
    responses=error_responses,
)
def get_statement_budget_recommendations(
    statement_uuid: UUID,
    *,
    service: Annotated[
        BudgetService,
        Depends(get_budget_service),
    ],
) -> ApiResponse[BudgetRecommendationResult]:
    """Generate deterministic budget recommendations with AI guidance."""

    result = service.generate_statement_budget_recommendations(
        statement_uuid=statement_uuid,
    )
    return ApiResponse(
        message="Statement budget recommendations generated successfully.",
        data=result,
    )


@router.get(
    "/{statement_uuid}/monthly-report",
    response_model=ApiResponse[MonthlyFinancialReportResult],
    status_code=status.HTTP_200_OK,
    responses=error_responses,
)
def get_statement_monthly_report(
    statement_uuid: UUID,
    *,
    service: Annotated[
        FinancialReportService,
        Depends(get_financial_report_service),
    ],
) -> ApiResponse[MonthlyFinancialReportResult]:
    """Generate AI-powered monthly report built on deterministic analysis modules."""

    result = service.generate_monthly_report(statement_uuid=statement_uuid)
    return ApiResponse(
        message="Statement monthly report generated successfully.",
        data=result,
    )
