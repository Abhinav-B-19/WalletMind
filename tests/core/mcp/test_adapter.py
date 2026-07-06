from __future__ import annotations

from backend.app.mcp.adapter import WalletMindMCPAdapter
from backend.app.mcp.models import ToolMetadata
from backend.app.mcp.registry import MCPToolRegistry


def test_adapter_initialization() -> None:
    registry = MCPToolRegistry()
    adapter = WalletMindMCPAdapter(registry=registry)

    assert adapter.initialized is True
    assert adapter.list_bound_tools() == []


def test_adapter_binds_tool_metadata() -> None:
    registry = MCPToolRegistry()
    adapter = WalletMindMCPAdapter(registry=registry)

    tool = ToolMetadata(name="infra_tool", description="Infra only")
    bound = adapter.bind_tool_metadata(tool=tool)

    assert bound.name == "infra_tool"
    assert [item.name for item in adapter.list_bound_tools()] == ["infra_tool"]
