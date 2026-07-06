"""ADK Function Tool for WalletMind assistant chat delegation."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from google.adk.tools import FunctionTool
from pydantic import BaseModel, Field

from backend.app.services.assistant.financial_assistant_service import (
    AssistantChatRequest,
    FinancialAssistantService,
)


class AssistantToolInput(BaseModel):
    """Validated input for assistant chat tool execution."""

    statement_id: UUID
    question: str = Field(..., min_length=1, max_length=500)


class AssistantToolOutput(BaseModel):
    """Structured output returned by the assistant chat tool."""

    statement_id: UUID
    delegated_service: str = "FinancialAssistantService"
    data: dict[str, Any]


def _resolve_service(
    service: FinancialAssistantService | None,
) -> FinancialAssistantService:
    if service is not None:
        return service

    from backend.app.main import app

    resolved = getattr(app.state, "financial_assistant_service", None)
    if resolved is None:
        raise RuntimeError("financial_assistant_service is not configured on app.state")
    return resolved


def _model_dump(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return value
    raise TypeError(
        "Financial assistant service result must be dict-like or Pydantic model"
    )


def run_assistant_tool(
    *,
    statement_id: str,
    question: str,
    service: FinancialAssistantService | None = None,
    logger: logging.Logger | None = None,
) -> dict[str, Any]:
    """Validate input and delegate to FinancialAssistantService."""

    tool_logger = logger or logging.getLogger(__name__)
    payload = AssistantToolInput(statement_id=statement_id, question=question)
    resolved_service = _resolve_service(service)

    tool_logger.info(
        "Assistant tool execution started.",
        extra={"statement_id": str(payload.statement_id)},
    )
    try:
        result = resolved_service.chat(
            AssistantChatRequest(
                statement_id=payload.statement_id,
                question=payload.question,
            )
        )
    except Exception:
        tool_logger.exception(
            "Assistant tool execution failed.",
            extra={"statement_id": str(payload.statement_id)},
        )
        raise

    output = AssistantToolOutput(
        statement_id=payload.statement_id,
        data=_model_dump(result),
    )
    tool_logger.info(
        "Assistant tool execution completed.",
        extra={"statement_id": str(payload.statement_id)},
    )
    return output.model_dump(mode="json")


def assistant_tool(statement_id: str, question: str) -> dict[str, Any]:
    """ADK callable that delegates assistant chat to WalletMind service."""

    return run_assistant_tool(statement_id=statement_id, question=question)


ASSISTANT_TOOL = FunctionTool(func=assistant_tool)

__all__ = [
    "ASSISTANT_TOOL",
    "AssistantToolInput",
    "AssistantToolOutput",
    "assistant_tool",
    "run_assistant_tool",
]
