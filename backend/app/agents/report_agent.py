"""Specialized ADK agent for monthly report tool orchestration."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from google.adk import Agent
from google.adk.tools import FunctionTool
from pydantic import BaseModel

from backend.app.agents.base_agent import WalletMindBaseAgent
from backend.app.agents.context import AgentExecutionContext
from backend.app.agents.types import AgentMetadata
from backend.app.tools.report_tool import REPORT_TOOL


class ReportAgentInput(BaseModel):
    """Validated input contract for `ReportAgent` execution."""

    statement_uuid: UUID


class ReportAgent(WalletMindBaseAgent):
    """ADK-backed specialized agent that executes WalletMind report tool only."""

    def __init__(
        self,
        *,
        tool: FunctionTool = REPORT_TOOL,
        logger: logging.Logger | None = None,
    ) -> None:
        super().__init__(
            metadata=AgentMetadata(
                name="report_agent",
                description=(
                    "Specialized WalletMind agent that executes monthly reporting "
                    "through the ADK ReportTool."
                ),
                tags=("report", "monthly_report", "summary"),
            ),
            logger=logger,
        )
        self._tool = tool

    @property
    def capabilities(self) -> tuple[str, ...]:
        """Return declared capabilities for agent discovery and planning."""

        return self.metadata.tags

    @property
    def typed_adk_agent(self) -> Agent:
        """Return this specialized agent as an official Google ADK `Agent`."""

        return self.adk_agent

    def build_adk_agent_kwargs(self) -> dict[str, Any]:
        """Build ADK agent configuration with exactly one registered Function Tool."""

        return {"tools": [self._tool]}

    def validate(self, *, context: AgentExecutionContext) -> None:
        """Validate context envelope and report input payload."""

        super().validate(context=context)
        ReportAgentInput.model_validate(context.extras or {})

    async def execute_impl(self, *, context: AgentExecutionContext) -> Any:
        """Execute exactly one ADK Function Tool and return structured payload."""

        payload = ReportAgentInput.model_validate(context.extras or {})
        tool_result = await self._tool.run_async(
            args={"statement_uuid": str(payload.statement_uuid)},
            tool_context=(context.extras or {}).get("adk_tool_context"),
        )
        return {
            "agent": self.metadata.name,
            "tool": self._tool.name,
            "result": tool_result,
            "context": {
                "user_id": context.user_id,
                "session_id": context.session_id,
                "has_session_service": context.session_service is not None,
                "has_memory_service": context.memory_service is not None,
            },
        }
