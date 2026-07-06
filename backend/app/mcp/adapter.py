"""WalletMind MCP adapter abstraction.

Sprint 2.1 provides only adapter scaffolding. No WalletMind tools are registered.
"""

from __future__ import annotations

from backend.app.mcp.models import ToolMetadata
from backend.app.mcp.registry import MCPToolRegistry


class WalletMindMCPAdapter:
    """Bridge abstraction from future ADK tools to MCP registry bindings."""

    def __init__(self, *, registry: MCPToolRegistry) -> None:
        self._registry = registry
        self._initialized = True

    @property
    def initialized(self) -> bool:
        """Return adapter initialization status."""

        return self._initialized

    def bind_tool_metadata(self, *, tool: ToolMetadata) -> ToolMetadata:
        """Bind transport-level metadata without registering WalletMind tools yet."""

        return self._registry.register_tool(tool=tool)

    def list_bound_tools(self) -> list[ToolMetadata]:
        """Return currently bound tool metadata entries."""

        return self._registry.discover_all()
