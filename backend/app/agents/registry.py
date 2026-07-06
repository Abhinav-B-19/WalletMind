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
        self._capability_index: dict[str, set[str]] = {}

    @staticmethod
    def _normalize_capability(capability: str) -> str:
        return capability.strip().lower()

    @staticmethod
    def _infer_name(agent: object) -> str:
        metadata = getattr(agent, "metadata", None)
        metadata_name = getattr(metadata, "name", None)
        if isinstance(metadata_name, str) and metadata_name.strip():
            return metadata_name.strip()
        agent_name = getattr(agent, "name", None)
        if isinstance(agent_name, str) and agent_name.strip():
            return agent_name.strip()
        raise ValueError("Unable to infer agent name; provide `name` explicitly.")

    @staticmethod
    def _infer_capabilities(agent: object) -> tuple[str, ...]:
        capabilities = getattr(agent, "capabilities", None)
        if capabilities is not None:
            return tuple(str(item) for item in capabilities)
        metadata = getattr(agent, "metadata", None)
        tags = getattr(metadata, "tags", None)
        if tags is not None:
            return tuple(str(item) for item in tags)
        return ()

    def _clear_indexes_for_name(self, name: str) -> None:
        for names in self._capability_index.values():
            names.discard(name)

    def register(
        self,
        *,
        agent: object,
        name: str | None = None,
        capabilities: Iterable[str] | None = None,
    ) -> None:
        """Register an agent instance with optional capability metadata."""

        resolved_name = (
            name.strip() if isinstance(name, str) else self._infer_name(agent)
        )
        resolved_capabilities = (
            tuple(capabilities)
            if capabilities is not None
            else self._infer_capabilities(agent)
        )

        self._clear_indexes_for_name(resolved_name)
        self._agents[resolved_name] = agent

        for capability in resolved_capabilities:
            normalized = self._normalize_capability(capability)
            if not normalized:
                continue
            self._capability_index.setdefault(normalized, set()).add(resolved_name)

    def discover_by_name(self, name: str) -> object | None:
        """Return an agent by name when registered, otherwise None."""

        return self._agents.get(name)

    def discover_all(self) -> tuple[object, ...]:
        """Return all registered agents."""

        return tuple(self._agents.values())

    def discover_by_capability(self, capability: str) -> tuple[object, ...]:
        """Return agents advertising the requested capability."""

        normalized = self._normalize_capability(capability)
        agent_names = self._capability_index.get(normalized, set())
        return tuple(self._agents[name] for name in sorted(agent_names))

    def get(self, name: str) -> object | None:
        """Backward-compatible alias for `discover_by_name()`."""

        return self.discover_by_name(name)

    def list_names(self) -> Iterable[str]:
        """Return all registered agent names sorted for deterministic discovery."""

        return tuple(sorted(self._agents.keys()))
