"""ADK Function Tool for WalletMind spending insights delegation."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from google.adk.tools import FunctionTool
from pydantic import BaseModel

from backend.app.services.analysis.spending_insights_service import (
    SpendingInsightsService,
)


class InsightsToolInput(BaseModel):
    """Validated input for spending insights tool execution."""

    statement_uuid: UUID


class InsightsToolOutput(BaseModel):
    """Structured output returned by the spending insights tool."""

    statement_uuid: UUID
    delegated_service: str = "SpendingInsightsService"
    data: dict[str, Any]


def _resolve_service(
    service: SpendingInsightsService | None,
) -> SpendingInsightsService:
    if service is not None:
        return service

    from backend.app.main import app

    resolved = getattr(app.state, "spending_insights_service", None)
    if resolved is None:
        raise RuntimeError("spending_insights_service is not configured on app.state")
    return resolved


def _model_dump(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return value
    raise TypeError(
        "Spending insights service result must be dict-like or Pydantic model"
    )


def run_insights_tool(
    *,
    statement_uuid: str,
    service: SpendingInsightsService | None = None,
    logger: logging.Logger | None = None,
) -> dict[str, Any]:
    """Validate input and delegate to SpendingInsightsService."""

    tool_logger = logger or logging.getLogger(__name__)
    payload = InsightsToolInput(statement_uuid=statement_uuid)
    resolved_service = _resolve_service(service)

    tool_logger.info(
        "Insights tool execution started.",
        extra={"statement_uuid": str(payload.statement_uuid)},
    )
    try:
        result = resolved_service.generate_statement_insights(
            statement_uuid=payload.statement_uuid,
        )
    except Exception:
        tool_logger.exception(
            "Insights tool execution failed.",
            extra={"statement_uuid": str(payload.statement_uuid)},
        )
        raise

    output = InsightsToolOutput(
        statement_uuid=payload.statement_uuid,
        data=_model_dump(result),
    )
    tool_logger.info(
        "Insights tool execution completed.",
        extra={"statement_uuid": str(payload.statement_uuid)},
    )
    return output.model_dump(mode="json")


def insights_tool(statement_uuid: str) -> dict[str, Any]:
    """ADK callable that delegates insights generation to WalletMind service."""

    return run_insights_tool(statement_uuid=statement_uuid)


INSIGHTS_TOOL = FunctionTool(func=insights_tool)

__all__ = [
    "INSIGHTS_TOOL",
    "InsightsToolInput",
    "InsightsToolOutput",
    "insights_tool",
    "run_insights_tool",
]
