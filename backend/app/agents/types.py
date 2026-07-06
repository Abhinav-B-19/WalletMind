"""Shared types for WalletMind's agent layer.

These types are framework-level infrastructure for future WalletMind agents.
They intentionally contain no business logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any


class AgentExecutionStatus(StrEnum):
    """Standardized execution lifecycle status values for agents and traces."""

    STARTED = "STARTED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


@dataclass(frozen=True)
class AgentExecutionTraceStep:
    """Transport-agnostic execution trace step for an agent invocation."""

    agent_name: str
    started_at: datetime
    ended_at: datetime
    duration_ms: float
    status: AgentExecutionStatus


@dataclass(frozen=True)
class AgentMetadata:
    """Common metadata attached to every WalletMind agent."""

    name: str
    description: str
    version: str = "1.0.0"
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class AgentExecutionResult:
    """Standardized execution result for all WalletMind agents."""

    status: AgentExecutionStatus
    agent_name: str
    execution_time: float
    metadata: AgentMetadata
    errors: list[str]
    result: Any | None
    trace: tuple[AgentExecutionTraceStep, ...] = ()
