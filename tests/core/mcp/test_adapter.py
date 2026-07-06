from __future__ import annotations

import asyncio
from types import SimpleNamespace

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


class FakeFunctionTool:
    def _get_declaration(self):
        return {
            "name": "fake_tool",
            "description": "Fake ADK tool",
            "parameters_json_schema": {
                "type": "object",
                "properties": {"value": {"type": "string"}},
                "required": ["value"],
            },
            "response_json_schema": {
                "type": "object",
                "properties": {"echo": {"type": "string"}},
            },
        }

    async def run_async(self, *, args, tool_context):
        _ = tool_context
        return {"echo": args["value"]}


class FakeCoordinator:
    runtime = None

    async def execute(self, *, context):
        return SimpleNamespace(
            result={
                "overall_status": "COMPLETED",
                "query": context.message,
                "inputs": context.extras["inputs"],
            }
        )


def test_adapter_binds_adk_function_tool_with_executable_handler() -> None:
    registry = MCPToolRegistry()
    adapter = WalletMindMCPAdapter(registry=registry)

    metadata = adapter.bind_adk_function_tool(adk_tool=FakeFunctionTool())

    assert metadata.name == "fake_tool"
    handler = registry.discover_handler(name="fake_tool")
    assert handler is not None
    result = asyncio.run(handler({"value": "hello"}))
    assert result == {"echo": "hello"}


def test_adapter_binds_analyze_finances_orchestration_tool() -> None:
    registry = MCPToolRegistry()
    adapter = WalletMindMCPAdapter(registry=registry)

    metadata = adapter.bind_analyze_finances_tool(coordinator=FakeCoordinator())

    assert metadata.name == "analyze_finances"
    handler = registry.discover_handler(name="analyze_finances")
    assert handler is not None

    result = asyncio.run(
        handler(
            {
                "query": "Analyze my finances",
                "user_id": "user-1",
                "session_id": "session-1",
                "inputs": {"statement_uuid": "11111111-1111-1111-1111-111111111111"},
            }
        )
    )
    assert result["overall_status"] == "COMPLETED"
    assert result["query"] == "Analyze my finances"
