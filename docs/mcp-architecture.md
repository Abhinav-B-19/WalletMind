# MCP Architecture (Sprint 2.2)

## Purpose

Sprint 2.2 exposes existing WalletMind capabilities through MCP by reusing:

- Existing Google ADK Function Tools
- Existing CoordinatorAgent orchestration

No WalletMind business logic is duplicated or moved.

## Why MCP

Model Context Protocol (MCP) adds a standardized interface between agent runtimes
and external tool ecosystems. For WalletMind, this enables future expansion to
external MCP-capable hosts while preserving deterministic business services and
existing ADK orchestration boundaries.

## Scope for Sprint 2.2

Included:

- Standalone MCP server with official FastMCP streamable HTTP mount
- Adapter-driven registration of existing ADK Function Tools
- MCP orchestration tool `analyze_finances` backed by CoordinatorAgent
- MCP execution endpoint for registered tool handlers
- Improved metadata SDK reporting and production server identity

Deferred to Sprint 2.3+:

- Auth enforcement implementation
- Session management implementation
- Streaming orchestration enhancements

## Target Flow

FastAPI
-> REST APIs
-> MCP Server
-> MCP Tool Registry
-> WalletMind MCP Adapter
-> Existing ADK Function Tools
-> WalletMind Services

## Component Responsibilities

### MCP Server

- Standalone startup/shutdown lifecycle
- Auto-bootstraps WalletMind MCP tools through adapter
- Tool registration, discovery, and execution via registry handlers
- Transport-level health and metadata endpoints
- Mounts official FastMCP streamable HTTP protocol app
- Future-ready capability declarations for auth/session/streaming hooks

### MCP Tool Registry

- register_tool()
- discover_tool()
- discover_all()
- unregister_tool()
- Tool metadata ownership at transport layer

### WalletMind MCP Adapter

- Maps existing ADK FunctionTool declarations into MCP metadata
- Binds executable handlers that call `FunctionTool.run_async(...)`
- Exposes `analyze_finances` orchestration tool that calls CoordinatorAgent

### Configuration

MCP server config is isolated in `backend/app/mcp/config.py` and supports:

- host/port
- logging level
- server identity
- transport mode
- auto-register tools flag
- auth feature flag and provider placeholder
- session management and streaming feature flags

Default server identity: `WalletMind MCP Server`

## Endpoints

- `GET /mcp/health`
- `GET /mcp/metadata`
- `GET /mcp/tools`
- `POST /mcp/tools/register`
- `DELETE /mcp/tools/{tool_name}`
- `POST /mcp/tools/{tool_name}/execute`

## Relationship to Existing Architecture

- Coordinator remains orchestration-only.
- ADK Function Tools remain implemented in existing ADK layer and are reused.
- WalletMind services remain source of truth.
- Existing REST APIs and frontend flows remain unchanged.

Sprint 2.2 exposes the following MCP tools:

- `processing_tool`
- `health_tool`
- `insights_tool`
- `budget_tool`
- `report_tool`
- `assistant_tool`
- `analyze_finances`

`analyze_finances` delegates to CoordinatorAgent -> ADK workflow -> specialized
agents -> aggregated response.
