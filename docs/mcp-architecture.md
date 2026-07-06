# MCP Architecture (Sprint 2.1)

## Purpose

Sprint 2.1 introduces transport-level MCP infrastructure only.
No WalletMind business tools are exposed yet.

## Why MCP

Model Context Protocol (MCP) adds a standardized interface between agent runtimes
and external tool ecosystems. For WalletMind, this enables future expansion to
external MCP-capable hosts while preserving deterministic business services and
existing ADK orchestration boundaries.

## Scope for Sprint 2.1

Included:

- Standalone MCP infrastructure server
- MCP tool registry with dynamic registration/discovery lifecycle
- WalletMind MCP adapter abstraction
- MCP server configuration model
- Transport-level models and observability endpoints

Excluded (deferred to Sprint 2.2):

- WalletMind ADK Function Tool registration
- Business service exposure through MCP
- Any WalletMind financial logic in MCP transport layer

## Target Flow

FastAPI
-> REST APIs
-> MCP Server
-> MCP Tool Registry
-> WalletMind MCP Adapter
-> (ready for Sprint 2.2 tool bindings)

## Component Responsibilities

### MCP Server

- Standalone startup/shutdown lifecycle
- Tool registration and discovery operations via registry
- Transport-level health and metadata endpoints
- Future-ready capability declarations for auth/session/streaming hooks

### MCP Tool Registry

- register_tool()
- discover_tool()
- discover_all()
- unregister_tool()
- Tool metadata ownership at transport layer

### WalletMind MCP Adapter

- Abstraction for future ADK Function Tool to MCP mapping
- No WalletMind tool registration in Sprint 2.1

### Configuration

MCP server config is isolated in `backend/app/mcp/config.py` and supports:

- host/port
- logging level
- server identity
- transport mode
- auth feature flag and provider placeholder
- session management and streaming feature flags

## Endpoints (Infrastructure-only)

- `GET /mcp/health`
- `GET /mcp/metadata`
- `GET /mcp/tools`
- `POST /mcp/tools/register`
- `DELETE /mcp/tools/{tool_name}`

## Relationship to Existing Architecture

- Coordinator remains orchestration-only.
- ADK Function Tools remain inside existing ADK layer.
- WalletMind services remain source of truth.
- Existing REST APIs and frontend flows remain unchanged.

Sprint 2.2 will connect ADK Function Tools to MCP registry through the adapter.
