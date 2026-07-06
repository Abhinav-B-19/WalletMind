"""Coordinator ADK agent for multi-agent orchestration.

This module contains orchestration-only logic. It does not include any financial
business logic and does not call WalletMind domain services directly.
"""

from __future__ import annotations

import logging
from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any

from google.adk import Agent
from pydantic import BaseModel, Field

from backend.app.agents.base_agent import WalletMindBaseAgent
from backend.app.agents.context import AgentExecutionContext
from backend.app.agents.registry import AgentRegistry
from backend.app.agents.types import AgentExecutionStatus, AgentMetadata


class CoordinatorExecutionMode(str):
    """Supported orchestration execution modes."""

    SINGLE = "single"
    MULTI = "multi"


class OrchestrationRequest(BaseModel):
    """Input contract for coordinator orchestration execution."""

    query: str = Field(..., min_length=1, max_length=1000)
    user_id: str = Field(..., min_length=1)
    session_id: str = Field(..., min_length=1)
    inputs: dict[str, Any] = Field(default_factory=dict)


class DecisionRecord(BaseModel):
    """Structured orchestration decision record for observability."""

    intent: str
    capabilities: list[str]
    selected_agents: list[str]
    reason: str
    execution_mode: str
    execution_timestamp: datetime


class CoordinatorOrchestrationResult(BaseModel):
    """Final aggregated coordinator orchestration payload."""

    overall_status: AgentExecutionStatus
    decision_record: DecisionRecord
    execution_trace: list[dict[str, Any]]
    individual_agent_results: list[dict[str, Any]]
    metadata: dict[str, Any]


class CoordinatorAgent(WalletMindBaseAgent):
    """Real ADK coordinator agent for capability-based agent orchestration."""

    _SINGLE_INTENT_CAPABILITIES: tuple[tuple[str, tuple[str, ...]], ...] = (
        ("health", ("financial_health",)),
        ("insights", ("insights",)),
        ("budget", ("budget",)),
        ("report", ("monthly_report",)),
        ("assistant", ("chat",)),
        ("processing", ("processing",)),
    )

    _MULTI_INTENT_KEYWORDS: tuple[str, ...] = (
        "analyze",
        "analysis",
        "complete",
        "full",
        "overview",
        "all",
    )

    _MULTI_AGENT_CAPABILITIES_ORDERED: tuple[str, ...] = (
        "financial_health",
        "insights",
        "budget",
        "monthly_report",
        "chat",
    )

    def __init__(
        self,
        *,
        registry: AgentRegistry,
        workflow: Any | None = None,
        runtime: Any | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        super().__init__(
            metadata=AgentMetadata(
                name="coordinator_agent",
                description=(
                    "WalletMind coordinator agent for capability-based specialized "
                    "agent orchestration over ADK runtime primitives."
                ),
                tags=("coordinator", "orchestration", "workflow", "adk"),
            ),
            logger=logger,
        )
        self._registry = registry
        self.runtime = runtime
        self._workflow = workflow or getattr(runtime, "root_workflow", None)

    @property
    def capabilities(self) -> tuple[str, ...]:
        """Return coordinator capability descriptors."""

        return self.metadata.tags

    @property
    def typed_adk_agent(self) -> Agent:
        """Return this coordinator as an official Google ADK Agent."""

        return self.adk_agent

    def build_adk_agent_kwargs(self) -> dict[str, Any]:
        """Configure coordinator as an ADK agent without domain tool bindings."""

        return {"tools": []}

    def validate(self, *, context: AgentExecutionContext) -> None:
        """Validate orchestration payload in execution context extras."""

        super().validate(context=context)
        OrchestrationRequest.model_validate(context.extras or {})

    async def execute_impl(self, *, context: AgentExecutionContext) -> Any:
        """Perform capability resolution, agent execution, and aggregation."""

        request = OrchestrationRequest.model_validate(context.extras or {})
        intent = self._determine_intent(query=request.query)
        execution_mode = self._determine_execution_mode(
            intent=intent,
            query=request.query,
        )

        capabilities = self._resolve_capabilities(
            intent=intent,
            execution_mode=execution_mode,
        )
        selected_agents = self._discover_agents(capabilities=capabilities)
        workflow_descriptor = self._build_workflow_descriptor(
            execution_mode=execution_mode,
            selected_agents=[agent.metadata.name for agent in selected_agents],
        )

        decision_record = DecisionRecord(
            intent=intent,
            capabilities=list(capabilities),
            selected_agents=[agent.metadata.name for agent in selected_agents],
            reason=self._decision_reason(intent=intent, execution_mode=execution_mode),
            execution_mode=execution_mode,
            execution_timestamp=datetime.now(UTC),
        )

        workflow_name = getattr(self._workflow, "name", "walletmind_root_workflow")
        ordered_results: list[dict[str, Any]] = []
        isolated_failures = 0

        for index, agent in enumerate(selected_agents, start=1):
            started_at = datetime.now(UTC)
            try:
                agent_context = self._build_agent_context(
                    base_context=context,
                    request=request,
                    target_agent_name=agent.metadata.name,
                )
                result = await agent.execute(context=agent_context)
                result_payload = asdict(result)
                result_payload["status"] = result.status.value
                result_payload["trace"] = [
                    {
                        **asdict(step),
                        "status": step.status.value,
                    }
                    for step in result.trace
                ]
                ordered_results.append(result_payload)
                context.append_trace_step(
                    agent_name=agent.metadata.name,
                    started_at=started_at,
                    ended_at=datetime.now(UTC),
                    status=result.status,
                    execution_order=index,
                )
            except Exception as exc:  # noqa: BLE001
                isolated_failures += 1
                context.append_trace_step(
                    agent_name=agent.metadata.name,
                    started_at=started_at,
                    ended_at=datetime.now(UTC),
                    status=AgentExecutionStatus.FAILED,
                    execution_order=index,
                    error=str(exc),
                )
                ordered_results.append(
                    {
                        "status": AgentExecutionStatus.FAILED.value,
                        "agent_name": agent.metadata.name,
                        "execution_time": 0.0,
                        "metadata": asdict(agent.metadata),
                        "errors": [str(exc)],
                        "result": None,
                        "trace": [
                            {
                                "agent_name": agent.metadata.name,
                                "started_at": started_at,
                                "ended_at": datetime.now(UTC),
                                "duration_ms": 0.0,
                                "status": AgentExecutionStatus.FAILED.value,
                                "execution_order": index,
                                "error": str(exc),
                            }
                        ],
                    }
                )

        success_count = sum(
            1
            for item in ordered_results
            if item.get("status") == AgentExecutionStatus.COMPLETED.value
        )
        overall_status = (
            AgentExecutionStatus.COMPLETED
            if success_count > 0
            else AgentExecutionStatus.FAILED
        )

        execution_trace = [
            {**asdict(step), "status": step.status.value}
            for step in context.execution_trace
        ]

        aggregated = CoordinatorOrchestrationResult(
            overall_status=overall_status,
            decision_record=decision_record,
            execution_trace=execution_trace,
            individual_agent_results=ordered_results,
            metadata={
                "workflow_name": workflow_name,
                "workflow": workflow_descriptor,
                "runner_integrated": context.runner is not None,
                "selected_agent_count": len(selected_agents),
                "successful_agent_count": success_count,
                "failed_agent_count": isolated_failures,
            },
        )

        return aggregated.model_dump(mode="json")

    @staticmethod
    def _determine_intent(*, query: str) -> str:
        lowered = query.lower()
        for intent, _capabilities in CoordinatorAgent._SINGLE_INTENT_CAPABILITIES:
            if intent in lowered:
                return intent
        if any(
            keyword in lowered
            for keyword in CoordinatorAgent._MULTI_INTENT_KEYWORDS
        ):
            return "analyze_finances"
        return "unknown"

    @staticmethod
    def _determine_execution_mode(*, intent: str, query: str) -> str:
        if intent == "analyze_finances":
            return CoordinatorExecutionMode.MULTI
        if "complete" in query.lower() or "analyze" in query.lower():
            return CoordinatorExecutionMode.MULTI
        return CoordinatorExecutionMode.SINGLE

    def _resolve_capabilities(
        self,
        *,
        intent: str,
        execution_mode: str,
    ) -> tuple[str, ...]:
        if execution_mode == CoordinatorExecutionMode.MULTI:
            return self._MULTI_AGENT_CAPABILITIES_ORDERED

        for mapped_intent, mapped_capabilities in self._SINGLE_INTENT_CAPABILITIES:
            if mapped_intent == intent:
                return mapped_capabilities
        return ()

    def _discover_agents(self, *, capabilities: tuple[str, ...]) -> list[Any]:
        ordered: list[Any] = []
        seen_names: set[str] = set()
        for capability in capabilities:
            for candidate in self._registry.discover_by_capability(capability):
                name = candidate.metadata.name
                if name in seen_names:
                    continue
                seen_names.add(name)
                ordered.append(candidate)
        return ordered

    @staticmethod
    def _decision_reason(*, intent: str, execution_mode: str) -> str:
        if intent == "unknown":
            return "No clear specialized intent found; no agents selected."
        if execution_mode == CoordinatorExecutionMode.MULTI:
            return "Complex intent detected; selected multi-agent execution plan."
        return "Specific intent detected; selected single specialized agent execution."

    @staticmethod
    def _build_agent_context(
        *,
        base_context: AgentExecutionContext,
        request: OrchestrationRequest,
        target_agent_name: str,
    ) -> AgentExecutionContext:
        extras = dict(request.inputs)
        extras.setdefault("query", request.query)
        extras.setdefault("target_agent", target_agent_name)
        return AgentExecutionContext(
            user_id=request.user_id,
            session_id=request.session_id,
            message=request.query,
            runner=base_context.runner,
            session_service=base_context.session_service,
            memory_service=base_context.memory_service,
            extras=extras,
        )

    @staticmethod
    def _build_workflow_descriptor(
        *,
        execution_mode: str,
        selected_agents: list[str],
    ) -> dict[str, Any]:
        """Build transport-agnostic workflow metadata for orchestration execution."""

        return {
            "execution_mode": execution_mode,
            "strategy": "sequential",
            "supports_parallel_future": True,
            "supports_retries": True,
            "supports_failure_isolation": True,
            "selected_agents": selected_agents,
        }
