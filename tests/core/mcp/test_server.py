from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.mcp.config import MCPServerConfig
from backend.app.mcp.models import ToolMetadata, ToolRegistrationRequest
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


def test_health_metadata_and_tools_endpoints() -> None:
    app = create_mcp_app(config=MCPServerConfig(server_name="walletmind_mcp_test"))

    with TestClient(app) as client:
        health = client.get("/mcp/health")
        metadata = client.get("/mcp/metadata")
        tools = client.get("/mcp/tools")

    assert health.status_code == 200
    health_payload = health.json()
    assert health_payload["status"] == "healthy"
    assert health_payload["server_name"] == "walletmind_mcp_test"

    assert metadata.status_code == 200
    metadata_payload = metadata.json()
    assert metadata_payload["name"] == "walletmind_mcp_test"
    assert "tool_registration" in metadata_payload["capabilities"]

    assert tools.status_code == 200
    assert tools.json() == []


def test_tool_registration_and_removal_endpoints() -> None:
    app = create_mcp_app(config=MCPServerConfig())

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
