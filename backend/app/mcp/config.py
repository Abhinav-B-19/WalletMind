"""Configuration model for WalletMind MCP infrastructure."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class MCPServerConfig:
    """Runtime configuration for standalone MCP infrastructure server."""

    host: str = "127.0.0.1"
    port: int = 8100
    log_level: str = "info"
    server_name: str = "walletmind_mcp"
    server_version: str = "0.1.0"
    transport: str = "streamable-http"
    auth_enabled: bool = False
    auth_provider: str | None = None
    session_management_enabled: bool = False
    streaming_enabled: bool = False

    @classmethod
    def from_environment(cls) -> MCPServerConfig:
        """Build MCP server config from environment variables."""

        return cls(
            host=os.getenv("WALLETMIND_MCP_HOST", "127.0.0.1"),
            port=int(os.getenv("WALLETMIND_MCP_PORT", "8100")),
            log_level=os.getenv("WALLETMIND_MCP_LOG_LEVEL", "info"),
            server_name=os.getenv("WALLETMIND_MCP_SERVER_NAME", "walletmind_mcp"),
            server_version=os.getenv("WALLETMIND_MCP_SERVER_VERSION", "0.1.0"),
            transport=os.getenv("WALLETMIND_MCP_TRANSPORT", "streamable-http"),
            auth_enabled=(
                os.getenv("WALLETMIND_MCP_AUTH_ENABLED", "false").strip().lower()
                in {"1", "true", "yes", "on"}
            ),
            auth_provider=os.getenv("WALLETMIND_MCP_AUTH_PROVIDER"),
            session_management_enabled=(
                os.getenv(
                    "WALLETMIND_MCP_SESSION_MANAGEMENT_ENABLED",
                    "false",
                )
                .strip()
                .lower()
                in {"1", "true", "yes", "on"}
            ),
            streaming_enabled=(
                os.getenv("WALLETMIND_MCP_STREAMING_ENABLED", "false").strip().lower()
                in {"1", "true", "yes", "on"}
            ),
        )
