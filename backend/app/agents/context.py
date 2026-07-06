"""Execution context abstraction for WalletMind agent lifecycle."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from backend.app.agents.types import AgentExecutionStatus, AgentExecutionTraceStep


@dataclass
class AgentExecutionContext:
    """Context passed through WalletMindBaseAgent lifecycle hooks."""

    user_id: str
    session_id: str
    message: str
    runner: Any | None = None
    session_service: Any | None = None
    memory_service: Any | None = None
    extras: dict[str, Any] | None = None
    execution_status: AgentExecutionStatus | None = None
    execution_trace: list[AgentExecutionTraceStep] = field(default_factory=list)

    def mark_status(self, status: AgentExecutionStatus) -> None:
        """Set the latest execution lifecycle status for this context."""

        self.execution_status = status

    def append_trace_step(
        self,
        *,
        agent_name: str,
        started_at: datetime,
        ended_at: datetime,
        status: AgentExecutionStatus,
    ) -> AgentExecutionTraceStep:
        """Append a completed trace step to this execution context."""

        duration_ms = (ended_at - started_at).total_seconds() * 1000
        step = AgentExecutionTraceStep(
            agent_name=agent_name,
            started_at=started_at,
            ended_at=ended_at,
            duration_ms=duration_ms,
            status=status,
        )
        self.execution_trace.append(step)
        return step

    def mark_skipped(self, *, agent_name: str) -> AgentExecutionTraceStep:
        """Mark this context execution as skipped and append a zero-duration trace."""

        skipped_at = datetime.now(UTC)
        self.mark_status(AgentExecutionStatus.SKIPPED)
        return self.append_trace_step(
            agent_name=agent_name,
            started_at=skipped_at,
            ended_at=skipped_at,
            status=AgentExecutionStatus.SKIPPED,
        )
