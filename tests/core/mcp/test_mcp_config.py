from __future__ import annotations

from backend.app.mcp.config import MCPServerConfig


def test_mcp_config_defaults() -> None:
    config = MCPServerConfig()

    assert config.host == "127.0.0.1"
    assert config.port == 8100
    assert config.server_name == "walletmind_mcp"
    assert config.auth_enabled is False


def test_mcp_config_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("WALLETMIND_MCP_HOST", "0.0.0.0")
    monkeypatch.setenv("WALLETMIND_MCP_PORT", "8200")
    monkeypatch.setenv("WALLETMIND_MCP_LOG_LEVEL", "debug")
    monkeypatch.setenv("WALLETMIND_MCP_SERVER_NAME", "wm_mcp")
    monkeypatch.setenv("WALLETMIND_MCP_AUTH_ENABLED", "true")
    monkeypatch.setenv("WALLETMIND_MCP_SESSION_MANAGEMENT_ENABLED", "1")
    monkeypatch.setenv("WALLETMIND_MCP_STREAMING_ENABLED", "yes")

    config = MCPServerConfig.from_environment()

    assert config.host == "0.0.0.0"
    assert config.port == 8200
    assert config.log_level == "debug"
    assert config.server_name == "wm_mcp"
    assert config.auth_enabled is True
    assert config.session_management_enabled is True
    assert config.streaming_enabled is True
