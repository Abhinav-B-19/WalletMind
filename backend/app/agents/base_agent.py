"""WalletMind base agent abstraction aligned with Google ADK 2.x.

This class is a thin WalletMind infrastructure layer that composes with the
official ADK Agent type. It exists to provide common lifecycle behavior for
future domain agents while keeping runtime dependencies explicit.
"""

from __future__ import annotations

import importlib
import logging
from abc import ABC, abstractmethod
from time import perf_counter
from typing import Any

from backend.app.adk.runner import WalletMindRunner
from backend.app.agents.context import AgentExecutionContext
from backend.app.agents.response import failed_result, success_result
from backend.app.agents.types import AgentExecutionResult, AgentMetadata


class AdkAgentImportError(ImportError):
    """Raised when ADK Agent dependency is unavailable."""


class WalletMindBaseAgent(ABC):
    """Common lifecycle and ADK composition for WalletMind agents.

    Subclasses should implement only domain-specific execution in
    `execute_impl()` and ADK configuration details in `build_adk_agent_kwargs()`.
    """

    def __init__(
        self,
        *,
        metadata: AgentMetadata,
        logger: logging.Logger | None = None,
    ) -> None:
        self._metadata = metadata
        self._logger = logger or logging.getLogger(__name__)
        self._adk_agent: Any | None = None

    @property
    def metadata(self) -> AgentMetadata:
        """Return immutable metadata for this agent."""

        return self._metadata

    @property
    def adk_agent(self) -> Any:
        """Return lazily built official ADK Agent instance."""

        if self._adk_agent is None:
            agent_cls = self._load_adk_agent_class()
            kwargs = dict(self.build_adk_agent_kwargs())
            kwargs.setdefault("name", self._metadata.name)
            kwargs.setdefault("description", self._metadata.description)
            self._adk_agent = agent_cls(**kwargs)
        return self._adk_agent

    async def execute(
        self,
        *,
        context: AgentExecutionContext,
    ) -> AgentExecutionResult:
        """Run standardized lifecycle: validate -> before -> impl -> after."""

        started = perf_counter()
        self._logger.info(
            "Agent Started",
            extra={
                "agent_name": self._metadata.name,
                "session_id": context.session_id,
                "user_id": context.user_id,
            },
        )

        try:
            self.validate(context=context)
            await self.before_execute(context=context)
            impl_result = await self.execute_impl(context=context)
            execution_time = perf_counter() - started
            result = success_result(
                metadata=self._metadata,
                execution_time=execution_time,
                result=impl_result,
            )
            await self.after_execute(context=context, result=result)
            self._logger.info(
                "Agent Finished",
                extra={
                    "agent_name": self._metadata.name,
                    "session_id": context.session_id,
                    "user_id": context.user_id,
                    "execution_time": execution_time,
                    "status": result.status,
                },
            )
            return result
        except Exception as exc:
            execution_time = perf_counter() - started
            result = failed_result(
                metadata=self._metadata,
                execution_time=execution_time,
                errors=[str(exc)],
            )
            await self.after_execute(context=context, result=result)
            self._logger.exception(
                "Agent Finished",
                extra={
                    "agent_name": self._metadata.name,
                    "session_id": context.session_id,
                    "user_id": context.user_id,
                    "execution_time": execution_time,
                    "status": result.status,
                    "errors": result.errors,
                },
            )
            raise

    async def execute_with_runner(
        self,
        *,
        runner: WalletMindRunner,
        user_id: str,
        session_id: str,
        message: str,
    ) -> AgentExecutionResult:
        """Helper for ADK-runner integrated execution context."""

        context = AgentExecutionContext(
            user_id=user_id,
            session_id=session_id,
            message=message,
            runner=runner,
            session_service=runner.session_service,
        )
        return await self.execute(context=context)

    def validate(self, *, context: AgentExecutionContext) -> None:
        """Validate base execution preconditions."""

        if not context.message.strip():
            raise ValueError("Execution message must not be empty.")

    async def before_execute(self, *, context: AgentExecutionContext) -> None:
        """Lifecycle hook executed before `execute_impl()`."""

        _ = context

    async def after_execute(
        self,
        *,
        context: AgentExecutionContext,
        result: AgentExecutionResult,
    ) -> None:
        """Lifecycle hook executed after `execute_impl()`."""

        _ = (context, result)

    @abstractmethod
    async def execute_impl(self, *, context: AgentExecutionContext) -> Any:
        """Domain-specific execution implemented by concrete agents."""

    @abstractmethod
    def build_adk_agent_kwargs(self) -> dict[str, Any]:
        """Return ADK Agent kwargs specific to a concrete domain agent."""

    @staticmethod
    def _load_adk_agent_class() -> type[Any]:
        try:
            module = importlib.import_module("google.adk")
            return module.Agent
        except (ImportError, AttributeError) as exc:
            raise AdkAgentImportError(
                "google-adk 2.x with Agent is required. "
                "Install/upgrade with: pip install 'google-adk>=2.0'"
            ) from exc
