"""Transport-level models for MCP server infrastructure."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field


class ToolMetadata(BaseModel):
    """Metadata describing a registered MCP tool."""

    name: str = Field(..., min_length=1)
    description: str = Field(default="", max_length=500)
    version: str = Field(default="1.0.0", min_length=1, max_length=32)
    tags: tuple[str, ...] = ()
    input_schema: dict[str, object] = Field(default_factory=dict)
    output_schema: dict[str, object] = Field(default_factory=dict)
    enabled: bool = True


class ToolRegistrationRequest(BaseModel):
    """Request model for transport-level tool registration."""

    tool: ToolMetadata


class ToolRegistrationResponse(BaseModel):
    """Response model for transport-level tool registration."""

    success: bool
    message: str
    tool: ToolMetadata | None = None


class ToolExecutionRequest(BaseModel):
    """Request model for tool execution over MCP transport."""

    args: dict[str, object] = Field(default_factory=dict)


class ToolExecutionResponse(BaseModel):
    """Response model for tool execution over MCP transport."""

    success: bool
    tool_name: str
    result: dict[str, object] | None = None
    error: str | None = None


class ServerMetadata(BaseModel):
    """Metadata describing MCP server identity and capabilities."""

    name: str
    version: str
    sdk: str
    transport: str
    capabilities: tuple[str, ...]
    auth_enabled: bool
    session_management_enabled: bool
    streaming_enabled: bool
    started_at: datetime | None = None


class HealthResponse(BaseModel):
    """Server health model for observability endpoints."""

    status: str
    server_name: str
    registered_tools: int
    uptime_seconds: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
