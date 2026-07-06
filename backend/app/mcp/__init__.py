"""WalletMind MCP infrastructure package (Sprint 2.1).

This package provides transport-level MCP server primitives only.
No WalletMind business services, ADK tools, or domain logic are registered here.
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
