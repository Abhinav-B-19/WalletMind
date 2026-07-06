"""Coordinator orchestration API endpoint."""

from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from backend.app.adk.runtime import WalletMindAdkRuntime
from backend.app.agents.context import AgentExecutionContext
from backend.app.agents.coordinator_agent import CoordinatorAgent
from backend.app.api.dependencies import (
    get_coordinator_agent,
    get_statement_upload_service,
)
from backend.app.schemas.response import ApiResponse
from walletmind.services.statement_upload_service import StatementUploadService

router = APIRouter(prefix="/agents", tags=["agents"])


class AgentExecuteRequest(BaseModel):
    """Request payload for coordinator orchestration execution."""

    query: str = Field(..., min_length=1, max_length=1000)
    user_id: str = Field(default="orchestration-user", min_length=1)
    session_id: str = Field(default="orchestration-session", min_length=1)
    user_uuid: str | None = None
    inputs: dict[str, Any] = Field(default_factory=dict)


_PROCESSED_STATEMENT_STATUSES = {
    "ready_for_analysis",
    "analysis_pending",
    "parsed",
    "completed",
}


def _statement_field(statement: Any, field_name: str) -> Any:
    if isinstance(statement, dict):
        return statement.get(field_name)
    return getattr(statement, field_name, None)


def _statement_candidate_payload(statement: Any) -> dict[str, Any]:
    raw_uuid = _statement_field(statement, "statement_uuid")
    normalized_uuid = str(raw_uuid) if raw_uuid is not None else ""
    return {
        "statement_uuid": normalized_uuid,
        "original_filename": _statement_field(statement, "original_filename"),
        "status": str(_statement_field(statement, "status") or ""),
        "uploaded_at": _statement_field(statement, "uploaded_at"),
    }


def _resolve_statement_uuid(
    *,
    payload: AgentExecuteRequest,
    statement_upload_service: StatementUploadService,
) -> tuple[str | None, JSONResponse | None]:
    provided_statement_uuid = payload.inputs.get("statement_uuid")
    if provided_statement_uuid:
        return str(provided_statement_uuid), None

    user_uuid = payload.user_uuid or payload.inputs.get("user_uuid")
    if not user_uuid:
        return None, JSONResponse(
            status_code=422,
            content={
                "success": False,
                "code": "STATEMENT_SELECTION_REQUIRED",
                "message": (
                    "statement_uuid is missing. Provide statement_uuid directly, or "
                    "provide user_uuid so the coordinator can resolve the most recent "
                    "processed statement."
                ),
                "details": {
                    "required": ["statement_uuid"],
                    "optional_for_auto_resolution": ["user_uuid"],
                    "candidates": [],
                },
            },
        )

    statements = statement_upload_service.list_statements(
        user_uuid=UUID(str(user_uuid))
    )
    processed_candidates = [
        statement
        for statement in statements
        if str(_statement_field(statement, "status") or "")
        in _PROCESSED_STATEMENT_STATUSES
    ]

    if not processed_candidates:
        return None, JSONResponse(
            status_code=422,
            content={
                "success": False,
                "code": "NO_PROCESSED_STATEMENT",
                "message": (
                    "No processed statements were found for this user. Upload and "
                    "process a statement first, or provide statement_uuid explicitly."
                ),
                "details": {
                    "required": ["statement_uuid"],
                    "user_uuid": str(user_uuid),
                    "candidates": [],
                },
            },
        )

    if len(processed_candidates) > 1:
        candidates = [
            _statement_candidate_payload(statement)
            for statement in processed_candidates[:10]
        ]
        return None, JSONResponse(
            status_code=422,
            content={
                "success": False,
                "code": "MULTIPLE_PROCESSED_STATEMENTS",
                "message": (
                    "Multiple processed statements are available. Please choose one "
                    "and provide statement_uuid in the request inputs."
                ),
                "details": {
                    "required": ["statement_uuid"],
                    "user_uuid": str(user_uuid),
                    "candidates": candidates,
                },
            },
        )

    resolved_uuid = _statement_field(processed_candidates[0], "statement_uuid")
    return str(resolved_uuid), None


@router.post(
    "/execute",
    response_model=ApiResponse[dict[str, Any]],
    status_code=status.HTTP_200_OK,
)
async def execute_agents(
    payload: AgentExecuteRequest,
    coordinator: Annotated[CoordinatorAgent, Depends(get_coordinator_agent)],
    statement_upload_service: Annotated[
        StatementUploadService,
        Depends(get_statement_upload_service),
    ],
) -> ApiResponse[dict[str, Any]] | JSONResponse:
    """Execute coordinator-driven specialized ADK agent orchestration."""

    resolved_statement_uuid, resolution_error = _resolve_statement_uuid(
        payload=payload,
        statement_upload_service=statement_upload_service,
    )
    if resolution_error is not None:
        return resolution_error

    resolved_inputs = dict(payload.inputs)
    if resolved_statement_uuid is not None:
        resolved_inputs.setdefault("statement_uuid", resolved_statement_uuid)
        resolved_inputs.setdefault("statement_id", resolved_statement_uuid)

    runtime: WalletMindAdkRuntime | None = getattr(coordinator, "runtime", None)
    context = AgentExecutionContext(
        user_id=payload.user_id,
        session_id=payload.session_id,
        message=payload.query,
        runner=getattr(runtime, "runner", None),
        session_service=getattr(runtime, "session_service", None),
        memory_service=getattr(runtime, "memory_service", None),
        extras={
            "query": payload.query,
            "user_id": payload.user_id,
            "session_id": payload.session_id,
            "inputs": resolved_inputs,
        },
    )
    result = await coordinator.execute(context=context)
    return ApiResponse(
        message="Coordinator execution completed successfully.",
        data=result.result or {},
    )
