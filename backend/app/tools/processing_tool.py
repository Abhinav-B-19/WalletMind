"""ADK Function Tool for WalletMind statement processing delegation."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from google.adk.tools import FunctionTool
from pydantic import BaseModel, Field

from walletmind.services.statement_processing_service import StatementProcessingService


class ProcessingToolInput(BaseModel):
    """Validated input for statement processing tool execution."""

    statement_uuid: UUID
    original_filename: str = Field(..., min_length=1)
    stored_file_path: str = Field(..., min_length=1)
    content_type: str | None = None


class ProcessingToolOutput(BaseModel):
    """Structured output returned by the statement processing tool."""

    statement_uuid: UUID
    delegated_service: str = "StatementProcessingService"
    processing_invoked: bool = True


def _resolve_service(
    service: StatementProcessingService | None,
) -> StatementProcessingService:
    if service is not None:
        return service

    from backend.app.main import app

    resolved = getattr(app.state, "statement_processing_service", None)
    if resolved is None:
        raise RuntimeError(
            "statement_processing_service is not configured on app.state"
        )
    return resolved


def _logger_or_default(logger: logging.Logger | None) -> logging.Logger:
    return logger or logging.getLogger(__name__)


def run_processing_tool(
    *,
    statement_uuid: str,
    original_filename: str,
    stored_file_path: str,
    content_type: str | None = None,
    service: StatementProcessingService | None = None,
    logger: logging.Logger | None = None,
) -> dict[str, Any]:
    """Validate input and delegate processing to StatementProcessingService."""

    tool_logger = _logger_or_default(logger)
    payload = ProcessingToolInput(
        statement_uuid=statement_uuid,
        original_filename=original_filename,
        stored_file_path=stored_file_path,
        content_type=content_type,
    )
    resolved_service = _resolve_service(service)

    tool_logger.info(
        "Processing tool execution started.",
        extra={"statement_uuid": str(payload.statement_uuid)},
    )
    try:
        resolved_service.process_statement(
            statement_uuid=payload.statement_uuid,
            original_filename=payload.original_filename,
            stored_file_path=payload.stored_file_path,
            content_type=payload.content_type,
        )
    except Exception:
        tool_logger.exception(
            "Processing tool execution failed.",
            extra={"statement_uuid": str(payload.statement_uuid)},
        )
        raise

    output = ProcessingToolOutput(statement_uuid=payload.statement_uuid)
    tool_logger.info(
        "Processing tool execution completed.",
        extra={"statement_uuid": str(payload.statement_uuid)},
    )
    return output.model_dump(mode="json")


def processing_tool(
    statement_uuid: str,
    original_filename: str,
    stored_file_path: str,
    content_type: str | None = None,
) -> dict[str, Any]:
    """ADK callable that delegates statement processing to WalletMind service."""

    return run_processing_tool(
        statement_uuid=statement_uuid,
        original_filename=original_filename,
        stored_file_path=stored_file_path,
        content_type=content_type,
    )


PROCESSING_TOOL = FunctionTool(func=processing_tool)

__all__ = [
    "PROCESSING_TOOL",
    "ProcessingToolInput",
    "ProcessingToolOutput",
    "processing_tool",
    "run_processing_tool",
]
