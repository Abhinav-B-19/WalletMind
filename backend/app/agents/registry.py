"""Registry for WalletMind agents.

This is an infrastructure primitive used to register and discover agents
without coupling runtime code to concrete implementations.
"""

from __future__ import annotations

from collections.abc import Iterable


class AgentRegistry:
    """In-memory registry of WalletMind agent instances keyed by name."""

    def __init__(self) -> None:
        self._agents: dict[str, object] = {}

    def register(self, *, name: str, agent: object) -> None:
        """Register an agent instance by name."""

        self._agents[name] = agent

    def get(self, name: str) -> object | None:
        """Return an agent by name when registered, otherwise None."""

        return self._agents.get(name)

    def list_names(self) -> Iterable[str]:
        """Return all registered agent names."""

        return tuple(self._agents.keys())
