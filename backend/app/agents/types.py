"""Shared types for WalletMind's agent layer.

These types are framework-level infrastructure for future WalletMind agents.
They intentionally contain no business logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


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

    status: str
    agent_name: str
    execution_time: float
    metadata: AgentMetadata
    errors: list[str]
    result: Any | None
