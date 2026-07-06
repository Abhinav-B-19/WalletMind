"""WalletMind MCP adapter abstraction.

Sprint 2.2 maps existing ADK tools and coordinator orchestration to MCP transport.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from backend.app.agents.context import AgentExecutionContext
from backend.app.mcp.models import ToolMetadata
from backend.app.mcp.registry import MCPToolRegistry
from backend.app.tools import get_walletmind_function_tools

if TYPE_CHECKING:
    from google.adk.tools import FunctionTool


class MCPToolBindingError(RuntimeError):
    """Raised when MCP adapter cannot bind a tool."""


def _declaration_payload(tool: FunctionTool) -> dict[str, Any]:
    declaration_getter = getattr(tool, "_get_declaration", None)
    if declaration_getter is None:
        raise MCPToolBindingError("ADK tool does not expose declaration metadata")

    declaration = declaration_getter()
    if hasattr(declaration, "model_dump"):
        return declaration.model_dump(mode="json")
    if isinstance(declaration, dict):
        return declaration
    raise MCPToolBindingError("Unsupported ADK declaration payload type")


def _resolve_coordinator() -> Any:
    from backend.app.main import app

    coordinator = getattr(app.state, "coordinator_agent", None)
    if coordinator is None:
        raise MCPToolBindingError("coordinator_agent is not configured on app.state")
    return coordinator


def _resolve_runtime_context(coordinator: Any) -> tuple[Any, Any, Any, Any]:
    runtime = getattr(coordinator, "runtime", None)
    return (
        runtime,
        getattr(runtime, "runner", None),
        getattr(runtime, "session_service", None),
        getattr(runtime, "memory_service", None),
    )


class WalletMindMCPAdapter:
    """Bridge abstraction from future ADK tools to MCP registry bindings."""

    def __init__(self, *, registry: MCPToolRegistry) -> None:
        self._registry = registry
        self._initialized = True

    @property
    def initialized(self) -> bool:
        """Return adapter initialization status."""

        return self._initialized

    def bind_tool_metadata(self, *, tool: ToolMetadata) -> ToolMetadata:
        """Bind transport-level metadata only."""

        return self._registry.register_tool(tool=tool)

    def bind_adk_function_tool(
        self,
        *,
        adk_tool: FunctionTool,
        tags: tuple[str, ...] = ("walletmind", "adk", "function-tool"),
    ) -> ToolMetadata:
        """Bind an existing ADK FunctionTool into the MCP registry."""

        declaration = _declaration_payload(adk_tool)
        tool_name = str(declaration.get("name") or "unknown_tool")
        description = str(declaration.get("description") or "")
        input_schema = declaration.get("parameters_json_schema") or {}
        output_schema = declaration.get("response_json_schema") or {}

        metadata = ToolMetadata(
            name=tool_name,
            description=description,
            tags=tags,
            input_schema=input_schema,
            output_schema=output_schema,
            enabled=True,
        )

        async def _handler(args: dict[str, object]) -> dict[str, object]:
            result = await adk_tool.run_async(args=dict(args), tool_context=None)
            if hasattr(result, "model_dump"):
                return result.model_dump(mode="json")
            if isinstance(result, dict):
                return result
            return {"result": result}

        return self._registry.register_tool(tool=metadata, handler=_handler)

    def bind_analyze_finances_tool(
        self,
        *,
        coordinator: Any | None = None,
    ) -> ToolMetadata:
        """Bind coordinator orchestration as MCP tool without new business logic."""

        metadata = ToolMetadata(
            name="analyze_finances",
            description=(
                "Invoke existing WalletMind CoordinatorAgent orchestration for "
                "capability routing and aggregated financial analysis."
            ),
            tags=("walletmind", "coordinator", "orchestration"),
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "user_id": {"type": "string"},
                    "session_id": {"type": "string"},
                    "inputs": {"type": "object"},
                },
                "required": ["query", "user_id", "session_id"],
                "additionalProperties": False,
            },
            output_schema={
                "type": "object",
                "description": "Coordinator aggregated orchestration payload",
            },
            enabled=True,
        )

        async def _handler(args: dict[str, object]) -> dict[str, object]:
            resolved_coordinator = coordinator or _resolve_coordinator()
            query = str(args.get("query") or "").strip()
            user_id = str(args.get("user_id") or "").strip()
            session_id = str(args.get("session_id") or "").strip()
            inputs = args.get("inputs")

            if not query:
                raise MCPToolBindingError("analyze_finances requires non-empty query")
            if not user_id:
                raise MCPToolBindingError("analyze_finances requires user_id")
            if not session_id:
                raise MCPToolBindingError("analyze_finances requires session_id")
            if inputs is None:
                inputs = {}
            if not isinstance(inputs, dict):
                raise MCPToolBindingError("analyze_finances inputs must be an object")

            _runtime, runner, session_service, memory_service = (
                _resolve_runtime_context(resolved_coordinator)
            )
            context = AgentExecutionContext(
                user_id=user_id,
                session_id=session_id,
                message=query,
                runner=runner,
                session_service=session_service,
                memory_service=memory_service,
                extras={
                    "query": query,
                    "user_id": user_id,
                    "session_id": session_id,
                    "inputs": inputs,
                },
            )
            result = await resolved_coordinator.execute(context=context)
            payload = result.result or {}
            if isinstance(payload, dict):
                return payload
            if hasattr(payload, "model_dump"):
                return payload.model_dump(mode="json")
            return {"result": payload}

        return self._registry.register_tool(tool=metadata, handler=_handler)

    def bind_walletmind_function_tools(self) -> list[ToolMetadata]:
        """Bind all existing WalletMind ADK function tools into MCP registry."""

        bound: list[ToolMetadata] = []
        for adk_tool in get_walletmind_function_tools():
            bound.append(self.bind_adk_function_tool(adk_tool=adk_tool))
        return bound

    def bootstrap_walletmind_tools(self) -> list[ToolMetadata]:
        """Bind WalletMind ADK tools + coordinator orchestration tool."""

        tools = self.bind_walletmind_function_tools()
        tools.append(self.bind_analyze_finances_tool())
        return tools

    def list_bound_tools(self) -> list[ToolMetadata]:
        """Return currently bound tool metadata entries."""

        return self._registry.discover_all()
