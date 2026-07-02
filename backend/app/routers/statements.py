"""Statement upload and metadata management API endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from fastapi.responses import Response

from backend.app.api.dependencies import get_statement_upload_service
from backend.app.api.schemas import ErrorResponse
from walletmind.schemas.statement import UploadResponseDTO
from walletmind.services.statement_upload_service import StatementUploadService

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
    response_model=UploadResponseDTO,
    status_code=status.HTTP_201_CREATED,
    responses=error_responses,
)
async def upload_statement(
    user_uuid: UUID = Form(...),
    file: UploadFile = File(...),
    service: StatementUploadService = Depends(get_statement_upload_service),
) -> UploadResponseDTO:
    """Upload a statement file and persist metadata."""

    file_bytes = await file.read()
    return service.upload_statement(
        user_uuid=user_uuid,
        original_filename=file.filename or "",
        file_bytes=file_bytes,
    )


@router.get(
    "",
    response_model=list[UploadResponseDTO],
    status_code=status.HTTP_200_OK,
    responses=error_responses,
)
def list_statements(
    user_uuid: UUID | None = None,
    service: StatementUploadService = Depends(get_statement_upload_service),
) -> list[UploadResponseDTO]:
    """List all uploaded statement metadata records."""

    return service.list_statements(user_uuid=user_uuid)


@router.get(
    "/{statement_uuid}",
    response_model=UploadResponseDTO,
    status_code=status.HTTP_200_OK,
    responses=error_responses,
)
def get_statement(
    statement_uuid: UUID,
    service: StatementUploadService = Depends(get_statement_upload_service),
) -> UploadResponseDTO:
    """Get metadata for a single uploaded statement."""

    return service.get_statement(statement_uuid)


@router.delete(
    "/{statement_uuid}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=error_responses,
)
def delete_statement(
    statement_uuid: UUID,
    service: StatementUploadService = Depends(get_statement_upload_service),
) -> Response:
    """Delete statement metadata and the uploaded file."""

    service.delete_statement(statement_uuid)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
