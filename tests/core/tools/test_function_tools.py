from __future__ import annotations

import logging
from typing import Any
from unittest.mock import MagicMock

import pytest
from google.adk.tools import FunctionTool
from pydantic import BaseModel, ValidationError

from backend.app.tools import WALLETMIND_FUNCTION_TOOLS, get_walletmind_function_tools
from backend.app.tools.assistant_tool import ASSISTANT_TOOL, run_assistant_tool
from backend.app.tools.budget_tool import BUDGET_TOOL, run_budget_tool
from backend.app.tools.health_tool import HEALTH_TOOL, run_health_tool
from backend.app.tools.insights_tool import INSIGHTS_TOOL, run_insights_tool
from backend.app.tools.processing_tool import PROCESSING_TOOL, run_processing_tool
from backend.app.tools.report_tool import REPORT_TOOL, run_report_tool


class DummyModel(BaseModel):
    value: str


class StubProcessingService:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def process_statement(self, **kwargs: Any) -> None:
        self.calls.append(kwargs)


class StubHealthService:
    def __init__(self, *, result: Any) -> None:
        self.result = result
        self.calls: list[dict[str, Any]] = []

    def generate_statement_health_score(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        return self.result


class StubInsightsService:
    def __init__(self, *, result: Any) -> None:
        self.result = result
        self.calls: list[dict[str, Any]] = []

    def generate_statement_insights(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        return self.result


class StubBudgetService:
    def __init__(self, *, result: Any) -> None:
        self.result = result
        self.calls: list[dict[str, Any]] = []

    def generate_statement_budget_recommendations(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        return self.result


class StubReportService:
    def __init__(self, *, result: Any) -> None:
        self.result = result
        self.calls: list[dict[str, Any]] = []

    def generate_monthly_report(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        return self.result


class StubAssistantService:
    def __init__(self, *, result: Any) -> None:
        self.result = result
        self.calls: list[Any] = []

    def chat(self, payload: Any) -> Any:
        self.calls.append(payload)
        return self.result


def test_tool_collection_exposes_adk_function_tools() -> None:
    tools = get_walletmind_function_tools()

    assert tools == list(WALLETMIND_FUNCTION_TOOLS)
    assert len(tools) == 6
    assert all(isinstance(tool, FunctionTool) for tool in tools)


def test_tool_registration_has_declarations() -> None:
    for tool in [
        PROCESSING_TOOL,
        HEALTH_TOOL,
        INSIGHTS_TOOL,
        BUDGET_TOOL,
        REPORT_TOOL,
        ASSISTANT_TOOL,
    ]:
        declaration = tool._get_declaration()
        assert declaration is not None
        assert declaration.name == tool.name


def test_processing_tool_delegates_and_returns_structured_output() -> None:
    service = StubProcessingService()
    logger = MagicMock(spec=logging.Logger)

    result = run_processing_tool(
        statement_uuid="11111111-1111-1111-1111-111111111111",
        original_filename="statement.csv",
        stored_file_path="/tmp/statement.csv",
        content_type="text/csv",
        service=service,
        logger=logger,
    )

    assert result["delegated_service"] == "StatementProcessingService"
    assert result["processing_invoked"] is True
    assert len(service.calls) == 1
    assert service.calls[0]["original_filename"] == "statement.csv"
    assert logger.info.call_count == 2


def test_processing_tool_input_validation_error() -> None:
    service = StubProcessingService()

    with pytest.raises(ValidationError):
        run_processing_tool(
            statement_uuid="not-a-uuid",
            original_filename="statement.csv",
            stored_file_path="/tmp/statement.csv",
            service=service,
        )


def test_processing_tool_propagates_service_error_and_logs() -> None:
    service = StubProcessingService()
    logger = MagicMock(spec=logging.Logger)

    def _boom(**_: Any) -> None:
        raise RuntimeError("processing failed")

    service.process_statement = _boom  # type: ignore[method-assign]

    with pytest.raises(RuntimeError, match="processing failed"):
        run_processing_tool(
            statement_uuid="11111111-1111-1111-1111-111111111111",
            original_filename="statement.csv",
            stored_file_path="/tmp/statement.csv",
            service=service,
            logger=logger,
        )

    logger.exception.assert_called_once()


def test_health_tool_delegates_and_returns_structured_output() -> None:
    service = StubHealthService(result=DummyModel(value="health"))
    logger = MagicMock(spec=logging.Logger)

    result = run_health_tool(
        statement_uuid="11111111-1111-1111-1111-111111111111",
        service=service,
        logger=logger,
    )

    assert result["delegated_service"] == "FinancialHealthService"
    assert result["data"]["value"] == "health"
    assert len(service.calls) == 1
    assert logger.info.call_count == 2


def test_insights_tool_delegates_and_returns_structured_output() -> None:
    service = StubInsightsService(result={"summary": "ok"})

    result = run_insights_tool(
        statement_uuid="11111111-1111-1111-1111-111111111111",
        service=service,
    )

    assert result["delegated_service"] == "SpendingInsightsService"
    assert result["data"]["summary"] == "ok"
    assert len(service.calls) == 1


def test_budget_tool_delegates_and_returns_structured_output() -> None:
    service = StubBudgetService(
        result={"monthly_budget": {"food": {"recommended": 200}}}
    )

    result = run_budget_tool(
        statement_uuid="11111111-1111-1111-1111-111111111111",
        service=service,
    )

    assert result["delegated_service"] == "BudgetService"
    assert "monthly_budget" in result["data"]
    assert len(service.calls) == 1


def test_report_tool_delegates_and_returns_structured_output() -> None:
    service = StubReportService(result={"executive_summary": "summary"})

    result = run_report_tool(
        statement_uuid="11111111-1111-1111-1111-111111111111",
        service=service,
    )

    assert result["delegated_service"] == "FinancialReportService"
    assert result["data"]["executive_summary"] == "summary"
    assert len(service.calls) == 1


def test_assistant_tool_delegates_and_returns_structured_output() -> None:
    service = StubAssistantService(result={"answer": "hello", "confidence": 0.8})

    result = run_assistant_tool(
        statement_id="11111111-1111-1111-1111-111111111111",
        question="How much did I spend?",
        service=service,
    )

    assert result["delegated_service"] == "FinancialAssistantService"
    assert result["data"]["answer"] == "hello"
    assert len(service.calls) == 1


def test_tool_error_propagation_for_domain_tools() -> None:
    class FailingHealthService:
        def generate_statement_health_score(self, **kwargs: Any) -> Any:
            _ = kwargs
            raise RuntimeError("service failed")

    with pytest.raises(RuntimeError, match="service failed"):
        run_health_tool(
            statement_uuid="11111111-1111-1111-1111-111111111111",
            service=FailingHealthService(),
        )
