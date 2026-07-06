"""ADK Function Tool for WalletMind monthly report delegation."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from google.adk.tools import FunctionTool
from pydantic import BaseModel

from backend.app.services.report.financial_report_service import FinancialReportService


class ReportToolInput(BaseModel):
    """Validated input for monthly report tool execution."""

    statement_uuid: UUID


class ReportToolOutput(BaseModel):
    """Structured output returned by the monthly report tool."""

    statement_uuid: UUID
    delegated_service: str = "FinancialReportService"
    data: dict[str, Any]


def _resolve_service(service: FinancialReportService | None) -> FinancialReportService:
    if service is not None:
        return service

    from backend.app.main import app

    resolved = getattr(app.state, "financial_report_service", None)
    if resolved is None:
        raise RuntimeError("financial_report_service is not configured on app.state")
    return resolved


def _model_dump(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return value
    raise TypeError(
        "Financial report service result must be dict-like or Pydantic model"
    )


def run_report_tool(
    *,
    statement_uuid: str,
    service: FinancialReportService | None = None,
    logger: logging.Logger | None = None,
) -> dict[str, Any]:
    """Validate input and delegate to FinancialReportService."""

    tool_logger = logger or logging.getLogger(__name__)
    payload = ReportToolInput(statement_uuid=statement_uuid)
    resolved_service = _resolve_service(service)

    tool_logger.info(
        "Report tool execution started.",
        extra={"statement_uuid": str(payload.statement_uuid)},
    )
    try:
        result = resolved_service.generate_monthly_report(
            statement_uuid=payload.statement_uuid,
        )
    except Exception:
        tool_logger.exception(
            "Report tool execution failed.",
            extra={"statement_uuid": str(payload.statement_uuid)},
        )
        raise

    output = ReportToolOutput(
        statement_uuid=payload.statement_uuid,
        data=_model_dump(result),
    )
    tool_logger.info(
        "Report tool execution completed.",
        extra={"statement_uuid": str(payload.statement_uuid)},
    )
    return output.model_dump(mode="json")


def report_tool(statement_uuid: str) -> dict[str, Any]:
    """ADK callable that delegates monthly report generation to WalletMind service."""

    return run_report_tool(statement_uuid=statement_uuid)


REPORT_TOOL = FunctionTool(func=report_tool)

__all__ = [
    "REPORT_TOOL",
    "ReportToolInput",
    "ReportToolOutput",
    "report_tool",
    "run_report_tool",
]
