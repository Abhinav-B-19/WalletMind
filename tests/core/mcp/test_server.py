from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from backend.app.mcp.config import MCPServerConfig
from backend.app.mcp.models import (
    ToolExecutionRequest,
    ToolMetadata,
    ToolRegistrationRequest,
)
from backend.app.mcp.server import MCPInfrastructureServer, create_mcp_app


def test_server_startup_and_shutdown() -> None:
    server = MCPInfrastructureServer(config=MCPServerConfig())

    assert server.started_at is None
    server.startup()
    assert server.started_at is not None
    server.shutdown()
    assert server.started_at is None


def test_server_register_and_discover_tool() -> None:
    server = MCPInfrastructureServer(config=MCPServerConfig())

    request = ToolRegistrationRequest(
        tool=ToolMetadata(name="tool_one", description="First tool")
    )
    response = server.register_tool(request=request)

    assert response.success is True
    assert response.tool is not None
    assert response.tool.name == "tool_one"

    discovered = server.discover_tool(name="tool_one")
    assert discovered is not None
    assert discovered.description == "First tool"


def test_execute_tool_uses_registered_handler() -> None:
    server = MCPInfrastructureServer(
        config=MCPServerConfig(auto_register_walletmind_tools=False)
    )
    metadata = ToolMetadata(name="echo", description="Echo tool")

    async def handler(args):
        return {"echo": args["value"]}

    server.registry.register_tool(tool=metadata, handler=handler)
    response = server.execute_tool(
        tool_name="echo",
        request=ToolExecutionRequest(args={"value": "hello"}),
    )

    result = response if not hasattr(response, "__await__") else None
    if result is None:
        import asyncio

        result = asyncio.run(response)

    assert result.success is True
    assert result.tool_name == "echo"
    assert result.result == {"echo": "hello"}


def test_health_metadata_and_tools_endpoints() -> None:
    app = create_mcp_app(
        config=MCPServerConfig(
            server_name="WalletMind MCP Test Server",
            auto_register_walletmind_tools=False,
        )
    )

    with TestClient(app) as client:
        health = client.get("/mcp/health")
        metadata = client.get("/mcp/metadata")
        tools = client.get("/mcp/tools")

    assert health.status_code == 200
    health_payload = health.json()
    assert health_payload["status"] == "healthy"
    assert health_payload["server_name"] == "WalletMind MCP Test Server"

    assert metadata.status_code == 200
    metadata_payload = metadata.json()
    assert metadata_payload["name"] == "WalletMind MCP Test Server"
    assert metadata_payload["sdk"].startswith("mcp-python-sdk/")
    assert metadata_payload["sdk"] != "mcp-python-sdk/unavailable"
    assert "tool_registration" in metadata_payload["capabilities"]

    assert tools.status_code == 200
    assert tools.json() == []


def test_root_landing_endpoint_returns_dynamic_tool_count() -> None:
    app = create_mcp_app(config=MCPServerConfig(auto_register_walletmind_tools=True))

    with TestClient(app) as client:
        root = client.get("/")
        tools = client.get("/mcp/tools")

    assert root.status_code == 200
    payload = root.json()
    assert payload["service"] == "WalletMind MCP Server"
    assert payload["status"] == "running"
    assert payload["documentation"] == "/docs"
    assert payload["metadata"] == "/mcp/metadata"
    assert payload["tools"] == "/mcp/tools"
    assert isinstance(payload["version"], str)
    assert payload["registered_tools"] == len(tools.json())


def test_tool_registration_and_removal_endpoints() -> None:
    app = create_mcp_app(config=MCPServerConfig(auto_register_walletmind_tools=False))

    with TestClient(app) as client:
        register = client.post(
            "/mcp/tools/register",
            json={
                "tool": {
                    "name": "registry_tool",
                    "description": "Registry test tool",
                    "version": "1.0.0",
                    "tags": ["infra"],
                    "input_schema": {},
                    "output_schema": {},
                    "enabled": True,
                }
            },
        )
        list_after_register = client.get("/mcp/tools")
        unregister = client.delete("/mcp/tools/registry_tool")

    assert register.status_code == 200
    assert register.json()["success"] is True

    tools = list_after_register.json()
    assert len(tools) == 1
    assert tools[0]["name"] == "registry_tool"

    assert unregister.status_code == 200
    assert unregister.json()["success"] is True


def test_phase0_registry_initially_empty_when_auto_register_disabled() -> None:
    app = create_mcp_app(config=MCPServerConfig(auto_register_walletmind_tools=False))

    with TestClient(app) as client:
        tools = client.get("/mcp/tools")

    assert tools.status_code == 200
    assert tools.json() == []


def test_walletmind_tools_auto_registered_in_sprint_2_2() -> None:
    app = create_mcp_app(config=MCPServerConfig(auto_register_walletmind_tools=True))

    with TestClient(app) as client:
        tools = client.get("/mcp/tools")

    assert tools.status_code == 200
    names = {item["name"] for item in tools.json()}
    assert names == {
        "processing_tool",
        "health_tool",
        "insights_tool",
        "budget_tool",
        "report_tool",
        "assistant_tool",
        "analyze_finances",
    }


def test_health_tool_execution_endpoint() -> None:
    app = create_mcp_app(config=MCPServerConfig(auto_register_walletmind_tools=True))

    with TestClient(app) as client:
        response = client.post(
            "/mcp/tools/health_tool/execute",
            json={"args": {"statement_uuid": str(uuid.uuid4())}},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is False
    assert payload["tool_name"] == "health_tool"
    assert "was not found" in (payload["error"] or "")


def test_walletmind_function_tool_execution_matrix() -> None:
    app = create_mcp_app(config=MCPServerConfig(auto_register_walletmind_tools=True))

    statement_uuid = str(uuid.uuid4())
    tool_calls = [
        (
            "processing_tool",
            {
                "statement_uuid": statement_uuid,
                "original_filename": "sample.csv",
                "stored_file_path": "/tmp/sample.csv",
                "content_type": "text/csv",
            },
        ),
        ("health_tool", {"statement_uuid": statement_uuid}),
        ("insights_tool", {"statement_uuid": statement_uuid}),
        ("budget_tool", {"statement_uuid": statement_uuid}),
        ("report_tool", {"statement_uuid": statement_uuid}),
        (
            "assistant_tool",
            {
                "statement_id": statement_uuid,
                "question": "How is my spending pattern?",
            },
        ),
    ]

    with TestClient(app) as client:
        for tool_name, args in tool_calls:
            response = client.post(
                f"/mcp/tools/{tool_name}/execute",
                json={"args": args},
            )

            assert response.status_code == 200
            payload = response.json()
            assert payload["tool_name"] == tool_name
            assert payload["success"] in {True, False}


def test_analyze_finances_execution_endpoint() -> None:
    app = create_mcp_app(config=MCPServerConfig(auto_register_walletmind_tools=True))

    with TestClient(app) as client:
        response = client.post(
            "/mcp/tools/analyze_finances/execute",
            json={
                "args": {
                    "query": "Analyze my finances",
                    "user_id": "mcp-user",
                    "session_id": "mcp-session",
                    "inputs": {
                        "statement_uuid": str(uuid.uuid4()),
                        "statement_id": str(uuid.uuid4()),
                    },
                }
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["tool_name"] == "analyze_finances"
    assert payload["result"]["decision_record"]["execution_mode"] in {
        "single",
        "multi",
    }
