"""Reusable Runner wrapper for WalletMind ADK runtime.

This wrapper manages session lifecycle and workflow execution results without
embedding any business logic.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RunnerExecutionResult:
    """Structured output returned by WalletMindRunner."""

    session_id: str
    user_id: str
    final_response: str | None
    event_count: int


class WalletMindRunner:
    """Wrapper over ADK Runner that standardizes session-aware execution."""

    def __init__(
        self,
        *,
        runner: Any,
        session_service: Any,
        app_name: str,
        logger: logging.Logger | None = None,
    ) -> None:
        self._runner = runner
        self._session_service = session_service
        self._app_name = app_name
        self._logger = logger or logging.getLogger(__name__)

    @property
    def raw_runner(self) -> Any:
        """Expose raw ADK runner for advanced integrations."""

        return self._runner

    @property
    def session_service(self) -> Any:
        """Expose session service used by this runner."""

        return self._session_service

    async def ensure_session(
        self,
        *,
        user_id: str,
        session_id: str,
        state: dict[str, Any] | None = None,
    ) -> Any:
        """Create session when needed; return existing session when available."""

        existing = await self._try_get_session(user_id=user_id, session_id=session_id)
        if existing is not None:
            return existing

        create_kwargs: dict[str, Any] = {
            "app_name": self._app_name,
            "user_id": user_id,
            "session_id": session_id,
        }
        if state is not None:
            create_kwargs["state"] = state

        created = await self._session_service.create_session(**create_kwargs)
        return created

    async def run(
        self,
        *,
        user_id: str,
        session_id: str,
        message: str,
    ) -> RunnerExecutionResult:
        """Execute the root workflow and return a compact structured result."""

        await self.ensure_session(user_id=user_id, session_id=session_id)

        final_response: str | None = None
        event_count = 0
        async for event in self._runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=message,
        ):
            event_count += 1
            extracted = self._extract_text(event)
            if extracted:
                final_response = extracted

        self._logger.debug(
            "ADK workflow run completed.",
            extra={
                "user_id": user_id,
                "session_id": session_id,
                "event_count": event_count,
            },
        )

        return RunnerExecutionResult(
            session_id=session_id,
            user_id=user_id,
            final_response=final_response,
            event_count=event_count,
        )

    async def _try_get_session(self, *, user_id: str, session_id: str) -> Any | None:
        if not hasattr(self._session_service, "get_session"):
            return None

        return await self._session_service.get_session(
            app_name=self._app_name,
            user_id=user_id,
            session_id=session_id,
        )

    @staticmethod
    def _extract_text(event: Any) -> str | None:
        """Best-effort extraction for event text without SDK type coupling."""

        content = getattr(event, "content", None)
        if content is None:
            return None

        text = getattr(content, "text", None)
        if isinstance(text, str) and text.strip():
            return text.strip()

        parts = getattr(content, "parts", None)
        if not isinstance(parts, list):
            return None

        fragments: list[str] = []
        for part in parts:
            part_text = getattr(part, "text", None)
            if isinstance(part_text, str) and part_text.strip():
                fragments.append(part_text.strip())

        if not fragments:
            return None
        return "\n".join(fragments)
