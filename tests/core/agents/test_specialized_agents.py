from __future__ import annotations

import asyncio
import logging
from typing import Any
from unittest.mock import MagicMock

import pytest
from google.adk import Agent
from google.adk.tools import FunctionTool
from pydantic import ValidationError

from backend.app.agents.assistant_agent import AssistantAgent
from backend.app.agents.budget_agent import BudgetAgent
from backend.app.agents.context import AgentExecutionContext
from backend.app.agents.health_agent import HealthAgent
from backend.app.agents.insights_agent import InsightsAgent
from backend.app.agents.processing_agent import ProcessingAgent
from backend.app.agents.report_agent import ReportAgent
from backend.app.agents.types import AgentExecutionStatus


def _context(*, extras: dict[str, Any]) -> AgentExecutionContext:
    return AgentExecutionContext(
        user_id="user-1",
        session_id="session-1",
        message="run",
        session_service=object(),
        memory_service=object(),
        extras=extras,
    )


@pytest.mark.parametrize(
    ("agent_cls", "tool_name", "extras"),
    [
        (
            ProcessingAgent,
            "processing_tool_fn",
            {
                "statement_uuid": "11111111-1111-1111-1111-111111111111",
                "original_filename": "statement.csv",
                "stored_file_path": "/tmp/statement.csv",
                "content_type": "text/csv",
            },
        ),
        (
            HealthAgent,
            "health_tool_fn",
            {"statement_uuid": "11111111-1111-1111-1111-111111111111"},
        ),
        (
            InsightsAgent,
            "insights_tool_fn",
            {"statement_uuid": "11111111-1111-1111-1111-111111111111"},
        ),
        (
            BudgetAgent,
            "budget_tool_fn",
            {"statement_uuid": "11111111-1111-1111-1111-111111111111"},
        ),
        (
            ReportAgent,
            "report_tool_fn",
            {"statement_uuid": "11111111-1111-1111-1111-111111111111"},
        ),
        (
            AssistantAgent,
            "assistant_tool_fn",
            {
                "statement_id": "11111111-1111-1111-1111-111111111111",
                "question": "How much did I spend?",
            },
        ),
    ],
)
def test_specialized_agent_adk_init_and_tool_registration(
    agent_cls,
    tool_name: str,
    extras: dict[str, Any],
):
    calls: list[dict[str, Any]] = []

    def _tool_impl(**kwargs: Any) -> dict[str, Any]:
        calls.append(kwargs)
        return {"ok": True}

    _tool_impl.__name__ = tool_name
    tool = FunctionTool(func=_tool_impl)

    agent = agent_cls(tool=tool)
    adk_agent = agent.typed_adk_agent

    assert isinstance(adk_agent, Agent)
    assert len(adk_agent.tools) == 1
    assert adk_agent.tools[0] is tool
    assert agent.capabilities == agent.metadata.tags

    result = asyncio.run(agent.execute(context=_context(extras=extras)))

    assert result.status == AgentExecutionStatus.COMPLETED
    assert result.agent_name == agent.metadata.name
    assert result.metadata == agent.metadata
    assert result.errors == []
    assert len(result.trace) == 1
    assert result.trace[0].status == AgentExecutionStatus.COMPLETED
    assert result.result["tool"] == tool.name
    assert result.result["context"]["session_id"] == "session-1"
    assert result.result["context"]["has_session_service"] is True
    assert result.result["context"]["has_memory_service"] is True
    assert len(calls) == 1


def test_specialized_agent_input_validation_error() -> None:
    calls: list[dict[str, Any]] = []

    def _tool_impl(**kwargs: Any) -> dict[str, Any]:
        calls.append(kwargs)
        return {"ok": True}

    _tool_impl.__name__ = "health_tool_fn"
    tool = FunctionTool(func=_tool_impl)
    agent = HealthAgent(tool=tool)

    with pytest.raises(ValidationError):
        asyncio.run(
            agent.execute(
                context=_context(extras={"statement_uuid": "not-a-uuid"})
            )
        )

    assert calls == []


def test_specialized_agent_error_propagation_and_logging() -> None:
    def _tool_impl(**kwargs: Any) -> dict[str, Any]:
        _ = kwargs
        raise RuntimeError("tool failed")

    _tool_impl.__name__ = "health_tool_fn"
    tool = FunctionTool(func=_tool_impl)
    logger = MagicMock(spec=logging.Logger)

    agent = HealthAgent(tool=tool, logger=logger)

    with pytest.raises(RuntimeError, match="tool failed"):
        asyncio.run(
            agent.execute(
                context=_context(
                    extras={"statement_uuid": "11111111-1111-1111-1111-111111111111"}
                )
            )
        )

    assert logger.info.call_count >= 1
    logger.exception.assert_called_once()
