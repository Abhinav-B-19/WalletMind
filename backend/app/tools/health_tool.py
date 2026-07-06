"""ADK Function Tool for WalletMind financial health analysis delegation."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from google.adk.tools import FunctionTool
from pydantic import BaseModel

from backend.app.services.health.financial_health_service import FinancialHealthService


class HealthToolInput(BaseModel):
    """Validated input for financial health tool execution."""

    statement_uuid: UUID


class HealthToolOutput(BaseModel):
    """Structured output returned by the financial health tool."""

    statement_uuid: UUID
    delegated_service: str = "FinancialHealthService"
    data: dict[str, Any]


def _resolve_service(service: FinancialHealthService | None) -> FinancialHealthService:
    if service is not None:
        return service

    from backend.app.main import app

    resolved = getattr(app.state, "financial_health_service", None)
    if resolved is None:
        raise RuntimeError("financial_health_service is not configured on app.state")
    return resolved


def _model_dump(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return value
    raise TypeError(
        "Financial health service result must be dict-like or Pydantic model"
    )


def run_health_tool(
    *,
    statement_uuid: str,
    service: FinancialHealthService | None = None,
    logger: logging.Logger | None = None,
) -> dict[str, Any]:
    """Validate input and delegate to FinancialHealthService."""

    tool_logger = logger or logging.getLogger(__name__)
    payload = HealthToolInput(statement_uuid=statement_uuid)
    resolved_service = _resolve_service(service)

    tool_logger.info(
        "Health tool execution started.",
        extra={"statement_uuid": str(payload.statement_uuid)},
    )
    try:
        result = resolved_service.generate_statement_health_score(
            statement_uuid=payload.statement_uuid,
        )
    except Exception:
        tool_logger.exception(
            "Health tool execution failed.",
            extra={"statement_uuid": str(payload.statement_uuid)},
        )
        raise

    output = HealthToolOutput(
        statement_uuid=payload.statement_uuid,
        data=_model_dump(result),
    )
    tool_logger.info(
        "Health tool execution completed.",
        extra={"statement_uuid": str(payload.statement_uuid)},
    )
    return output.model_dump(mode="json")


def health_tool(statement_uuid: str) -> dict[str, Any]:
    """ADK callable that delegates health-score generation to WalletMind service."""

    return run_health_tool(statement_uuid=statement_uuid)


HEALTH_TOOL = FunctionTool(func=health_tool)

__all__ = [
    "HEALTH_TOOL",
    "HealthToolInput",
    "HealthToolOutput",
    "health_tool",
    "run_health_tool",
]
