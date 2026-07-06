"""WalletMind MCP server package.

Sprint 2.1 introduced MCP transport infrastructure.
Sprint 2.2 exposes existing ADK Function Tools and coordinator orchestration
through the MCP registry/adapter without moving business logic.
"""

from backend.app.mcp.adapter import WalletMindMCPAdapter
from backend.app.mcp.config import MCPServerConfig
from backend.app.mcp.registry import MCPToolRegistry
from backend.app.mcp.server import MCPInfrastructureServer, create_mcp_app

__all__ = [
    "MCPInfrastructureServer",
    "MCPServerConfig",
    "MCPToolRegistry",
    "WalletMindMCPAdapter",
    "create_mcp_app",
]
