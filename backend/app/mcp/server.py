"""Standalone MCP infrastructure server for WalletMind (Sprint 2.1).

This module is intentionally transport-level only and does not import
WalletMind business services or ADK function tools.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

import uvicorn
from fastapi import FastAPI

from backend.app.mcp.adapter import WalletMindMCPAdapter
from backend.app.mcp.config import MCPServerConfig
from backend.app.mcp.models import (
    HealthResponse,
    ServerMetadata,
    ToolMetadata,
    ToolRegistrationRequest,
    ToolRegistrationResponse,
)
from backend.app.mcp.registry import MCPToolNotFoundError, MCPToolRegistry

logger = logging.getLogger(__name__)


def _resolve_mcp_sdk_version() -> str:
    try:
        import importlib.metadata as metadata

        return metadata.version("mcp")
    except Exception:  # noqa: BLE001
        return "unavailable"


class MCPInfrastructureServer:
    """Standalone MCP infrastructure host with transport-level registry APIs."""

    def __init__(
        self,
        *,
        config: MCPServerConfig | None = None,
        registry: MCPToolRegistry | None = None,
        adapter: WalletMindMCPAdapter | None = None,
    ) -> None:
        self.config = config or MCPServerConfig.from_environment()
        self.registry = registry or MCPToolRegistry()
        self.adapter = adapter or WalletMindMCPAdapter(registry=self.registry)
        self.started_at: datetime | None = None
        self._mcp_sdk_server: Any | None = None

    def initialize_sdk_server(self) -> Any | None:
        """Initialize official MCP SDK server object when SDK is available."""

        if self._mcp_sdk_server is not None:
            return self._mcp_sdk_server

        try:
            from mcp.server.fastmcp import FastMCP
        except Exception:  # noqa: BLE001
            logger.info("MCP SDK unavailable; skipping SDK server object init.")
            return None

        self._mcp_sdk_server = FastMCP(self.config.server_name)
        return self._mcp_sdk_server

    def startup(self) -> None:
        """Mark server startup and initialize SDK state."""

        self.initialize_sdk_server()
        self.started_at = datetime.now(UTC)

    def shutdown(self) -> None:
        """Mark server shutdown state."""

        self.started_at = None

    def server_metadata(self) -> ServerMetadata:
        """Return static and runtime server metadata."""

        return ServerMetadata(
            name=self.config.server_name,
            version=self.config.server_version,
            sdk=f"mcp-python-sdk/{_resolve_mcp_sdk_version()}",
            transport=self.config.transport,
            capabilities=(
                "startup",
                "shutdown",
                "tool_registration",
                "tool_discovery",
                "auth_hook_ready",
                "session_management_hook_ready",
                "streaming_hook_ready",
            ),
            auth_enabled=self.config.auth_enabled,
            session_management_enabled=self.config.session_management_enabled,
            streaming_enabled=self.config.streaming_enabled,
            started_at=self.started_at,
        )

    def health(self) -> HealthResponse:
        """Return service health details for readiness checks."""

        now = datetime.now(UTC)
        uptime_seconds = 0.0
        if self.started_at is not None:
            uptime_seconds = max((now - self.started_at).total_seconds(), 0.0)

        return HealthResponse(
            status="healthy",
            server_name=self.config.server_name,
            registered_tools=self.registry.size,
            uptime_seconds=uptime_seconds,
            timestamp=now,
        )

    def register_tool(
        self,
        *,
        request: ToolRegistrationRequest,
    ) -> ToolRegistrationResponse:
        """Register a transport-level tool metadata entry."""

        tool = self.registry.register_tool(tool=request.tool)
        return ToolRegistrationResponse(
            success=True,
            message=f"Tool '{tool.name}' registered.",
            tool=tool,
        )

    def discover_tool(self, *, name: str) -> ToolMetadata | None:
        """Discover one tool by name."""

        return self.registry.discover_tool(name=name)

    def discover_all(self) -> list[ToolMetadata]:
        """Discover all tool metadata entries."""

        return self.registry.discover_all()

    def unregister_tool(self, *, name: str) -> ToolRegistrationResponse:
        """Unregister one tool by name."""

        try:
            removed = self.registry.unregister_tool(name=name)
        except MCPToolNotFoundError:
            return ToolRegistrationResponse(
                success=False,
                message=f"Tool '{name}' not found.",
                tool=None,
            )

        return ToolRegistrationResponse(
            success=True,
            message=f"Tool '{name}' unregistered.",
            tool=removed,
        )


def create_mcp_app(
    *,
    config: MCPServerConfig | None = None,
    server: MCPInfrastructureServer | None = None,
) -> FastAPI:
    """Create standalone FastAPI app hosting MCP infrastructure endpoints."""

    infrastructure_server = server or MCPInfrastructureServer(config=config)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        infrastructure_server.startup()
        try:
            yield
        finally:
            infrastructure_server.shutdown()

    app = FastAPI(
        title="WalletMind MCP Infrastructure Server",
        version=infrastructure_server.config.server_version,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    @app.get("/mcp/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        return infrastructure_server.health()

    @app.get("/mcp/metadata", response_model=ServerMetadata)
    async def metadata() -> ServerMetadata:
        return infrastructure_server.server_metadata()

    @app.get("/mcp/tools", response_model=list[ToolMetadata])
    async def list_tools() -> list[ToolMetadata]:
        return infrastructure_server.discover_all()

    @app.post("/mcp/tools/register", response_model=ToolRegistrationResponse)
    async def register_tool(
        request: ToolRegistrationRequest,
    ) -> ToolRegistrationResponse:
        return infrastructure_server.register_tool(request=request)

    @app.delete("/mcp/tools/{tool_name}", response_model=ToolRegistrationResponse)
    async def unregister_tool(tool_name: str) -> ToolRegistrationResponse:
        return infrastructure_server.unregister_tool(name=tool_name)

    app.state.mcp_infrastructure_server = infrastructure_server
    return app


def main() -> int:
    """Run MCP infrastructure server independently from WalletMind FastAPI app."""

    config = MCPServerConfig.from_environment()
    uvicorn.run(
        "backend.app.mcp.server:create_mcp_app",
        host=config.host,
        port=config.port,
        log_level=config.log_level,
        factory=True,
        reload=False,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
