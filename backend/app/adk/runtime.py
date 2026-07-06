"""ADK runtime bootstrap for WalletMind.

This module introduces the foundational runtime wiring that future agent
orchestration will build upon, while keeping existing APIs and business logic
unchanged.
"""

from __future__ import annotations

import importlib
import logging
from dataclasses import dataclass
from typing import Any

from backend.app.adk.config import AdkRuntimeSettings
from backend.app.adk.memory import WalletMindMemoryServiceFactory
from backend.app.adk.runner import WalletMindRunner
from backend.app.adk.session import WalletMindSessionServiceFactory
from backend.app.adk.workflow import WalletMindWorkflowFactory


class AdkRunnerImportError(ImportError):
    """Raised when ADK Runner dependency is unavailable."""


@dataclass(frozen=True)
class WalletMindAdkRuntime:
    """Container object for initialized ADK runtime components."""

    settings: AdkRuntimeSettings
    session_service: Any
    memory_service: Any
    root_workflow: Any
    runner: WalletMindRunner


class WalletMindAdkRuntimeFactory:
    """Factory for constructing runtime dependencies with dependency injection."""

    def __init__(
        self,
        *,
        settings: AdkRuntimeSettings | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._settings = settings or AdkRuntimeSettings.from_environment()
        self._logger = logger or logging.getLogger(__name__)

    def create(self) -> WalletMindAdkRuntime:
        """Build and return all ADK runtime foundation components."""

        session_service = WalletMindSessionServiceFactory(logger=self._logger).create()
        memory_service = WalletMindMemoryServiceFactory(logger=self._logger).create()
        root_workflow = WalletMindWorkflowFactory(
            settings=self._settings,
            logger=self._logger,
        ).create()

        runner_cls = self._load_runner_class()
        raw_runner = runner_cls(
            agent=root_workflow,
            app_name=self._settings.app_name,
            session_service=session_service,
            memory_service=memory_service,
        )

        runner = WalletMindRunner(
            runner=raw_runner,
            session_service=session_service,
            app_name=self._settings.app_name,
            logger=self._logger,
        )

        self._logger.info("WalletMind ADK runtime initialized.")
        return WalletMindAdkRuntime(
            settings=self._settings,
            session_service=session_service,
            memory_service=memory_service,
            root_workflow=root_workflow,
            runner=runner,
        )

    @staticmethod
    def _load_runner_class() -> type[Any]:
        try:
            module = importlib.import_module("google.adk.runners")
            return getattr(module, "Runner")
        except (ImportError, AttributeError) as exc:
            raise AdkRunnerImportError(
                "google-adk 2.x with Runner is required. "
                "Install/upgrade with: pip install 'google-adk>=2.0'"
            ) from exc
