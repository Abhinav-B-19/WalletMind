"""Execution context abstraction for WalletMind agent lifecycle."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AgentExecutionContext:
    """Context passed through WalletMindBaseAgent lifecycle hooks."""

    user_id: str
    session_id: str
    message: str
    runner: Any | None = None
    session_service: Any | None = None
    memory_service: Any | None = None
    extras: dict[str, Any] | None = None
