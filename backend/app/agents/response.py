"""Helper builders for standardized agent execution responses."""

from __future__ import annotations

from backend.app.agents.types import AgentExecutionResult, AgentMetadata


def success_result(
    *,
    metadata: AgentMetadata,
    execution_time: float,
    result: object | None,
) -> AgentExecutionResult:
    """Create a standardized success response."""

    return AgentExecutionResult(
        status="success",
        agent_name=metadata.name,
        execution_time=execution_time,
        metadata=metadata,
        errors=[],
        result=result,
    )


def failed_result(
    *,
    metadata: AgentMetadata,
    execution_time: float,
    errors: list[str],
    result: object | None = None,
) -> AgentExecutionResult:
    """Create a standardized failure response."""

    return AgentExecutionResult(
        status="failed",
        agent_name=metadata.name,
        execution_time=execution_time,
        metadata=metadata,
        errors=errors,
        result=result,
    )
