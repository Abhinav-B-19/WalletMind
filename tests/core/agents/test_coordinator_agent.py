from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

from google.adk import Agent

from backend.app.agents.context import AgentExecutionContext
from backend.app.agents.coordinator_agent import CoordinatorAgent
from backend.app.agents.registry import AgentRegistry
from backend.app.agents.types import (
    AgentExecutionResult,
    AgentExecutionStatus,
    AgentExecutionTraceStep,
    AgentMetadata,
)


class StubSpecializedAgent:
    def __init__(
        self,
        *,
        name: str,
        capabilities: tuple[str, ...],
        should_fail: bool = False,
    ) -> None:
        self.metadata = AgentMetadata(
            name=name,
            description=f"{name} description",
            tags=capabilities,
        )
        self.capabilities = capabilities
        self._should_fail = should_fail
        self.received_contexts: list[AgentExecutionContext] = []

    async def execute(self, *, context: AgentExecutionContext) -> AgentExecutionResult:
        self.received_contexts.append(context)
        if self._should_fail:
            raise RuntimeError(f"{self.metadata.name} failed")

        started = datetime.now(UTC)
        ended = datetime.now(UTC)
        trace = (
            AgentExecutionTraceStep(
                agent_name=self.metadata.name,
                started_at=started,
                ended_at=ended,
                duration_ms=max((ended - started).total_seconds() * 1000, 0.0),
                status=AgentExecutionStatus.COMPLETED,
                execution_order=1,
                error=None,
            ),
        )
        return AgentExecutionResult(
            status=AgentExecutionStatus.COMPLETED,
            agent_name=self.metadata.name,
            execution_time=0.0,
            metadata=self.metadata,
            errors=[],
            result={"ok": True, "target": self.metadata.name},
            trace=trace,
        )


def _context(query: str, inputs: dict[str, Any] | None = None) -> AgentExecutionContext:
    return AgentExecutionContext(
        user_id="user-1",
        session_id="session-1",
        message=query,
        runner=object(),
        session_service=object(),
        memory_service=object(),
        extras={
            "query": query,
            "user_id": "user-1",
            "session_id": "session-1",
            "inputs": inputs or {},
        },
    )


def test_coordinator_is_official_adk_agent() -> None:
    registry = AgentRegistry()
    coordinator = CoordinatorAgent(registry=registry)

    assert isinstance(coordinator.typed_adk_agent, Agent)


def test_coordinator_single_agent_execution() -> None:
    registry = AgentRegistry()
    health = StubSpecializedAgent(
        name="health_agent",
        capabilities=("health", "financial_health", "score", "risk"),
    )
    registry.register(agent=health)

    coordinator = CoordinatorAgent(
        registry=registry,
        workflow=SimpleNamespace(name="wmf"),
    )
    result = asyncio.run(coordinator.execute(context=_context("Generate health score")))

    assert result.status == AgentExecutionStatus.COMPLETED
    payload = result.result
    assert payload["overall_status"] == AgentExecutionStatus.COMPLETED.value
    assert payload["decision_record"]["execution_mode"] == "single"
    assert payload["decision_record"]["selected_agents"] == ["health_agent"]
    assert payload["metadata"]["runner_integrated"] is True
    assert payload["metadata"]["workflow_name"] == "wmf"


def test_coordinator_multi_agent_execution() -> None:
    registry = AgentRegistry()
    registry.register(
        agent=StubSpecializedAgent(
            name="health_agent",
            capabilities=("health", "financial_health", "score", "risk"),
        )
    )
    registry.register(
        agent=StubSpecializedAgent(
            name="insights_agent",
            capabilities=("insights", "spending", "analytics"),
        )
    )
    registry.register(
        agent=StubSpecializedAgent(
            name="budget_agent",
            capabilities=("budget", "planning", "savings"),
        )
    )

    coordinator = CoordinatorAgent(registry=registry)
    result = asyncio.run(coordinator.execute(context=_context("Analyze my finances")))

    payload = result.result
    assert payload["decision_record"]["execution_mode"] == "multi"
    assert payload["metadata"]["selected_agent_count"] == 3
    assert payload["metadata"]["successful_agent_count"] == 3
    assert payload["overall_status"] == AgentExecutionStatus.COMPLETED.value
    assert len(payload["individual_agent_results"]) == 3


def test_coordinator_failure_isolation() -> None:
    registry = AgentRegistry()
    registry.register(
        agent=StubSpecializedAgent(
            name="health_agent",
            capabilities=("health", "financial_health", "score", "risk"),
        )
    )
    registry.register(
        agent=StubSpecializedAgent(
            name="insights_agent",
            capabilities=("insights", "spending", "analytics"),
            should_fail=True,
        )
    )

    coordinator = CoordinatorAgent(registry=registry)
    result = asyncio.run(coordinator.execute(context=_context("Analyze my finances")))

    payload = result.result
    assert payload["metadata"]["failed_agent_count"] == 1
    assert payload["metadata"]["successful_agent_count"] == 1
    assert len(payload["individual_agent_results"]) == 2
    statuses = [item["status"] for item in payload["individual_agent_results"]]
    assert AgentExecutionStatus.COMPLETED.value in statuses
    assert AgentExecutionStatus.FAILED.value in statuses


def test_coordinator_unknown_intent() -> None:
    registry = AgentRegistry()
    coordinator = CoordinatorAgent(registry=registry)

    result = asyncio.run(
        coordinator.execute(context=_context("Tell me something random"))
    )
    payload = result.result

    assert payload["decision_record"]["intent"] == "unknown"
    assert payload["decision_record"]["selected_agents"] == []
    assert payload["overall_status"] == AgentExecutionStatus.FAILED.value


def test_coordinator_registry_integration_by_capability() -> None:
    registry = AgentRegistry()
    target = StubSpecializedAgent(
        name="assistant_agent",
        capabilities=("assistant", "financial_advice", "chat"),
    )
    registry.register(agent=target)

    coordinator = CoordinatorAgent(registry=registry)
    result = asyncio.run(coordinator.execute(context=_context("assistant advice")))
    payload = result.result

    assert payload["decision_record"]["selected_agents"] == ["assistant_agent"]


def test_coordinator_workflow_and_runner_metadata() -> None:
    registry = AgentRegistry()
    registry.register(
        agent=StubSpecializedAgent(
            name="report_agent",
            capabilities=("report", "monthly_report", "summary"),
        )
    )
    workflow = SimpleNamespace(name="walletmind_coordinator_workflow")
    coordinator = CoordinatorAgent(registry=registry, workflow=workflow)

    result = asyncio.run(coordinator.execute(context=_context("generate report")))
    payload = result.result

    assert payload["metadata"]["workflow_name"] == "walletmind_coordinator_workflow"
    assert payload["metadata"]["runner_integrated"] is True
    assert payload["metadata"]["workflow"]["strategy"] == "sequential"


def test_coordinator_builds_agent_specific_payload_contracts() -> None:
    registry = AgentRegistry()
    health = StubSpecializedAgent(
        name="health_agent",
        capabilities=("health", "financial_health", "score", "risk"),
    )
    assistant = StubSpecializedAgent(
        name="assistant_agent",
        capabilities=("assistant", "financial_advice", "chat"),
    )
    registry.register(agent=health)
    registry.register(agent=assistant)

    coordinator = CoordinatorAgent(registry=registry)
    result = asyncio.run(
        coordinator.execute(
            context=_context(
                "Analyze my finances",
                inputs={
                    "statement_uuid": "11111111-1111-1111-1111-111111111111",
                    "statement_id": "11111111-1111-1111-1111-111111111111",
                },
            )
        )
    )

    assert result.status == AgentExecutionStatus.COMPLETED
    assert len(health.received_contexts) == 1
    assert len(assistant.received_contexts) == 1

    health_payload = health.received_contexts[0].extras
    assistant_payload = assistant.received_contexts[0].extras

    assert health_payload == {
        "statement_uuid": "11111111-1111-1111-1111-111111111111"
    }
    assert assistant_payload == {
        "statement_id": "11111111-1111-1111-1111-111111111111",
        "question": "Analyze my finances",
    }


def test_coordinator_five_agent_orchestration_success_summary() -> None:
    registry = AgentRegistry()
    registry.register(
        agent=StubSpecializedAgent(
            name="health_agent",
            capabilities=("health", "financial_health", "score", "risk"),
        )
    )
    registry.register(
        agent=StubSpecializedAgent(
            name="insights_agent",
            capabilities=("insights", "spending", "analytics"),
        )
    )
    registry.register(
        agent=StubSpecializedAgent(
            name="budget_agent",
            capabilities=("budget", "planning", "savings"),
        )
    )
    registry.register(
        agent=StubSpecializedAgent(
            name="report_agent",
            capabilities=("report", "monthly_report", "summary"),
        )
    )
    registry.register(
        agent=StubSpecializedAgent(
            name="assistant_agent",
            capabilities=("assistant", "financial_advice", "chat"),
        )
    )

    coordinator = CoordinatorAgent(registry=registry)
    result = asyncio.run(
        coordinator.execute(
            context=_context(
                "Analyze my finances",
                inputs={
                    "statement_uuid": "11111111-1111-1111-1111-111111111111",
                    "statement_id": "11111111-1111-1111-1111-111111111111",
                },
            )
        )
    )

    payload = result.result
    assert payload["overall_status"] == AgentExecutionStatus.COMPLETED.value
    assert payload["metadata"]["selected_agent_count"] == 5
    assert payload["metadata"]["successful_agent_count"] == 5
    assert payload["metadata"]["failed_agent_count"] == 0
    assert [step["status"] for step in payload["execution_trace"]] == [
        AgentExecutionStatus.COMPLETED.value,
        AgentExecutionStatus.COMPLETED.value,
        AgentExecutionStatus.COMPLETED.value,
        AgentExecutionStatus.COMPLETED.value,
        AgentExecutionStatus.COMPLETED.value,
    ]
