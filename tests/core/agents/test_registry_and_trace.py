from __future__ import annotations

from datetime import UTC, datetime, timedelta

from backend.app.agents.assistant_agent import AssistantAgent
from backend.app.agents.budget_agent import BudgetAgent
from backend.app.agents.context import AgentExecutionContext
from backend.app.agents.health_agent import HealthAgent
from backend.app.agents.registry import AgentRegistry
from backend.app.agents.types import AgentExecutionStatus


def test_agent_registry_capability_registration_and_discovery() -> None:
    registry = AgentRegistry()
    health = HealthAgent()
    budget = BudgetAgent()
    assistant = AssistantAgent()

    registry.register(agent=health)
    registry.register(agent=budget)
    registry.register(agent=assistant)

    health_discovery = registry.discover_by_capability("financial_health")
    budget_discovery = registry.discover_by_capability("savings")
    assistant_discovery = registry.discover_by_capability("chat")

    assert health in health_discovery
    assert budget in budget_discovery
    assert assistant in assistant_discovery
    assert registry.discover_by_name("health_agent") is health
    assert set(registry.list_names()) == {
        "assistant_agent",
        "budget_agent",
        "health_agent",
    }


def test_agent_registry_discover_all() -> None:
    registry = AgentRegistry()
    health = HealthAgent()
    budget = BudgetAgent()

    registry.register(agent=health)
    registry.register(agent=budget)

    discovered = registry.discover_all()

    assert health in discovered
    assert budget in discovered
    assert len(discovered) == 2


def test_execution_context_trace_creation_and_status_lifecycle() -> None:
    context = AgentExecutionContext(
        user_id="user-1",
        session_id="session-1",
        message="run",
    )

    context.mark_status(AgentExecutionStatus.STARTED)

    started_at = datetime.now(UTC)
    ended_at = started_at + timedelta(milliseconds=42)
    step = context.append_trace_step(
        agent_name="health_agent",
        started_at=started_at,
        ended_at=ended_at,
        status=AgentExecutionStatus.COMPLETED,
    )

    context.mark_status(AgentExecutionStatus.COMPLETED)

    assert context.execution_status == AgentExecutionStatus.COMPLETED
    assert len(context.execution_trace) == 1
    assert step.agent_name == "health_agent"
    assert step.status == AgentExecutionStatus.COMPLETED
    assert step.duration_ms > 0


def test_execution_context_mark_skipped() -> None:
    context = AgentExecutionContext(
        user_id="user-1",
        session_id="session-1",
        message="run",
    )

    step = context.mark_skipped(agent_name="report_agent")

    assert context.execution_status == AgentExecutionStatus.SKIPPED
    assert len(context.execution_trace) == 1
    assert step.agent_name == "report_agent"
    assert step.status == AgentExecutionStatus.SKIPPED
    assert step.duration_ms == 0
