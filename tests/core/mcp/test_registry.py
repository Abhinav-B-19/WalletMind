from __future__ import annotations

import pytest

from backend.app.mcp.models import ToolMetadata
from backend.app.mcp.registry import MCPToolNotFoundError, MCPToolRegistry


def test_registry_register_and_discover() -> None:
    registry = MCPToolRegistry()
    metadata = ToolMetadata(name="tool_a", description="A")
    handler = object()

    registered = registry.register_tool(tool=metadata, handler=handler)

    assert registered.name == "tool_a"
    discovered = registry.discover_tool(name="tool_a")
    assert discovered is not None
    assert discovered.description == "A"
    assert registry.discover_handler(name="tool_a") is handler


def test_registry_discover_all_sorted() -> None:
    registry = MCPToolRegistry()
    registry.register_tool(tool=ToolMetadata(name="zeta", description="Z"))
    registry.register_tool(tool=ToolMetadata(name="alpha", description="A"))

    tools = registry.discover_all()

    assert [tool.name for tool in tools] == ["alpha", "zeta"]


def test_registry_unregister() -> None:
    registry = MCPToolRegistry()
    registry.register_tool(tool=ToolMetadata(name="tool_a", description="A"))

    removed = registry.unregister_tool(name="tool_a")

    assert removed.name == "tool_a"
    assert registry.discover_tool(name="tool_a") is None


def test_registry_unregister_missing_raises() -> None:
    registry = MCPToolRegistry()

    with pytest.raises(MCPToolNotFoundError):
        registry.unregister_tool(name="missing")
