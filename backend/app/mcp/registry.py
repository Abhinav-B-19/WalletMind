"""Transport-level MCP tool registry."""

from __future__ import annotations

from dataclasses import dataclass

from backend.app.mcp.models import ToolMetadata


class MCPToolNotFoundError(KeyError):
    """Raised when a requested tool is not present in the registry."""


@dataclass(frozen=True)
class RegisteredMCPTool:
    """Internal representation for a registered tool and optional callable."""

    metadata: ToolMetadata
    handler: object | None = None


class MCPToolRegistry:
    """Registry for transport-layer MCP tool metadata and handlers."""

    def __init__(self) -> None:
        self._tools: dict[str, RegisteredMCPTool] = {}

    def register_tool(
        self,
        *,
        tool: ToolMetadata,
        handler: object | None = None,
    ) -> ToolMetadata:
        """Register or overwrite a tool by name and return normalized metadata."""

        self._tools[tool.name] = RegisteredMCPTool(metadata=tool, handler=handler)
        return tool

    def discover_tool(self, *, name: str) -> ToolMetadata | None:
        """Return a tool by name if it exists."""

        entry = self._tools.get(name)
        return entry.metadata if entry else None

    def discover_handler(self, *, name: str) -> object | None:
        """Return a registered execution handler by tool name."""

        entry = self._tools.get(name)
        return entry.handler if entry else None

    def discover_all(self) -> list[ToolMetadata]:
        """Return all registered tools sorted by tool name."""

        return [self._tools[name].metadata for name in sorted(self._tools.keys())]

    def unregister_tool(self, *, name: str) -> ToolMetadata:
        """Remove a tool by name and return the removed metadata."""

        try:
            entry = self._tools.pop(name)
        except KeyError as exc:
            raise MCPToolNotFoundError(name) from exc
        return entry.metadata

    def clear(self) -> None:
        """Remove all registered tools."""

        self._tools.clear()

    @property
    def size(self) -> int:
        """Return number of registered tools."""

        return len(self._tools)
