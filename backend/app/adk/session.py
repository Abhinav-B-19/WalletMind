"""Session service abstractions for WalletMind ADK runtime.

Session service is abstracted so future persistent implementations can replace
in-memory storage without changing runtime orchestration code.
"""

from __future__ import annotations

import importlib
import logging
from typing import Any


class AdkSessionImportError(ImportError):
    """Raised when ADK session dependencies are unavailable."""


class WalletMindSessionServiceFactory:
    """Factory for creating ADK session services.

    Uses ADK in-memory session storage for Sprint 1.1 while exposing a stable
    creation seam for future persistent backends.
    """

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger(__name__)

    def create(self) -> Any:
        """Create and return the configured ADK SessionService instance."""

        service_cls = self._load_in_memory_session_service()
        service = service_cls()
        self._logger.debug("Initialized ADK InMemorySessionService.")
        return service

    @staticmethod
    def _load_in_memory_session_service() -> type[Any]:
        try:
            module = importlib.import_module("google.adk.sessions")
            return getattr(module, "InMemorySessionService")
        except (ImportError, AttributeError) as exc:
            raise AdkSessionImportError(
                "google-adk 2.x with InMemorySessionService is required. "
                "Install/upgrade with: pip install 'google-adk>=2.0'"
            ) from exc
