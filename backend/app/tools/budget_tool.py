"""ADK Function Tool for WalletMind budget recommendations delegation."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from google.adk.tools import FunctionTool
from pydantic import BaseModel

from backend.app.services.budget.budget_service import BudgetService


class BudgetToolInput(BaseModel):
    """Validated input for budget recommendation tool execution."""

    statement_uuid: UUID


class BudgetToolOutput(BaseModel):
    """Structured output returned by the budget recommendation tool."""

    statement_uuid: UUID
    delegated_service: str = "BudgetService"
    data: dict[str, Any]


def _resolve_service(service: BudgetService | None) -> BudgetService:
    if service is not None:
        return service

    from backend.app.main import app

    resolved = getattr(app.state, "budget_service", None)
    if resolved is None:
        raise RuntimeError("budget_service is not configured on app.state")
    return resolved


def _model_dump(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return value
    raise TypeError("Budget service result must be dict-like or Pydantic model")


def run_budget_tool(
    *,
    statement_uuid: str,
    service: BudgetService | None = None,
    logger: logging.Logger | None = None,
) -> dict[str, Any]:
    """Validate input and delegate to BudgetService."""

    tool_logger = logger or logging.getLogger(__name__)
    payload = BudgetToolInput(statement_uuid=statement_uuid)
    resolved_service = _resolve_service(service)

    tool_logger.info(
        "Budget tool execution started.",
        extra={"statement_uuid": str(payload.statement_uuid)},
    )
    try:
        result = resolved_service.generate_statement_budget_recommendations(
            statement_uuid=payload.statement_uuid,
        )
    except Exception:
        tool_logger.exception(
            "Budget tool execution failed.",
            extra={"statement_uuid": str(payload.statement_uuid)},
        )
        raise

    output = BudgetToolOutput(
        statement_uuid=payload.statement_uuid,
        data=_model_dump(result),
    )
    tool_logger.info(
        "Budget tool execution completed.",
        extra={"statement_uuid": str(payload.statement_uuid)},
    )
    return output.model_dump(mode="json")


def budget_tool(statement_uuid: str) -> dict[str, Any]:
    """ADK callable that delegates budget recommendations to WalletMind service."""

    return run_budget_tool(statement_uuid=statement_uuid)


BUDGET_TOOL = FunctionTool(func=budget_tool)

__all__ = [
    "BUDGET_TOOL",
    "BudgetToolInput",
    "BudgetToolOutput",
    "budget_tool",
    "run_budget_tool",
]
