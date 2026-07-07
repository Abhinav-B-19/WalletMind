"""Standalone MCP infrastructure server for WalletMind (Sprint 2.1).

This module is intentionally transport-level only and does not import
WalletMind business services or ADK function tools.
"""

from __future__ import annotations

import inspect
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
    ToolExecutionRequest,
    ToolExecutionResponse,
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
        pass

    try:
        import mcp

        module_version = getattr(mcp, "__version__", None)
        if isinstance(module_version, str) and module_version.strip():
            return module_version
    except Exception:  # noqa: BLE001
        pass

    return "not-detected"


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

    def _bind_fastmcp_tools(self, *, tools: list[ToolMetadata]) -> None:
        """Register registry-backed handlers on FastMCP instance when available."""

        if self._mcp_sdk_server is None:
            return

        def _make_fastmcp_handler(
            *,
            tool_name: str,
            description: str,
            handler: Any,
        ):
            async def fastmcp_handler(**kwargs: Any) -> Any:
                result = handler(dict(kwargs))
                if inspect.isawaitable(result):
                    result = await result
                return result

            fastmcp_handler.__name__ = f"mcp_{tool_name}"
            fastmcp_handler.__doc__ = description or f"MCP tool: {tool_name}"
            return fastmcp_handler

        for tool in tools:
            handler = self.registry.discover_handler(name=tool.name)
            if handler is None:
                continue

            fastmcp_handler = _make_fastmcp_handler(
                tool_name=tool.name,
                description=tool.description,
                handler=handler,
            )
            self._mcp_sdk_server.add_tool(
                fn=fastmcp_handler,
                name=tool.name,
                description=tool.description or None,
            )

    def startup(self) -> None:
        """Mark server startup and initialize SDK state."""

        self.initialize_sdk_server()
        registered_count = 0
        if self.config.auto_register_walletmind_tools:
            tools = self.adapter.bootstrap_walletmind_tools()
            registered_count = len(tools)
            self._bind_fastmcp_tools(tools=tools)
        self.started_at = datetime.now(UTC)
        logger.info(
            "MCP infrastructure server started.",
            extra={
                "server_name": self.config.server_name,
                "server_version": self.config.server_version,
                "sdk": _resolve_mcp_sdk_version(),
                "registered_tools": registered_count,
            },
        )

    def shutdown(self) -> None:
        """Mark server shutdown state."""

        self.started_at = None
        logger.info("MCP infrastructure server stopped.")

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

    async def execute_tool(
        self,
        *,
        tool_name: str,
        request: ToolExecutionRequest,
    ) -> ToolExecutionResponse:
        """Execute a registered MCP tool handler."""

        handler = self.registry.discover_handler(name=tool_name)
        if handler is None:
            return ToolExecutionResponse(
                success=False,
                tool_name=tool_name,
                result=None,
                error=f"Tool '{tool_name}' is not registered.",
            )

        try:
            result = handler(dict(request.args))
            if inspect.isawaitable(result):
                result = await result
        except Exception as exc:  # noqa: BLE001
            return ToolExecutionResponse(
                success=False,
                tool_name=tool_name,
                result=None,
                error=str(exc),
            )

        if isinstance(result, dict):
            payload = result
        elif hasattr(result, "model_dump"):
            payload = result.model_dump(mode="json")
        else:
            payload = {"result": result}

        return ToolExecutionResponse(
            success=True,
            tool_name=tool_name,
            result=payload,
            error=None,
        )


def create_mcp_app(
    *,
    config: MCPServerConfig | None = None,
    server: MCPInfrastructureServer | None = None,
) -> FastAPI:
    """Create standalone FastAPI app hosting MCP infrastructure endpoints."""

    infrastructure_server = server or MCPInfrastructureServer(config=config)
    infrastructure_server.initialize_sdk_server()

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

    @app.get("/")
    async def root() -> dict[str, object]:
        return {
            "service": "WalletMind MCP Server",
            "description": (
                "Standalone Model Context Protocol (MCP) server exposing WalletMind "
                "AI capabilities."
            ),
            "status": "running",
            "version": infrastructure_server.config.server_version,
            "documentation": "/docs",
            "metadata": "/mcp/metadata",
            "health": "/mcp/health",
            "tools": "/mcp/tools",
            "transport": infrastructure_server.config.transport,
            "registered_tools": infrastructure_server.registry.size,
        }

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

    @app.post(
        "/mcp/tools/{tool_name}/execute",
        response_model=ToolExecutionResponse,
    )
    async def execute_tool(
        tool_name: str,
        request: ToolExecutionRequest,
    ) -> ToolExecutionResponse:
        return await infrastructure_server.execute_tool(
            tool_name=tool_name,
            request=request,
        )

    if infrastructure_server._mcp_sdk_server is not None:
        app.mount(
            "/mcp/protocol",
            infrastructure_server._mcp_sdk_server.streamable_http_app(),
        )

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
