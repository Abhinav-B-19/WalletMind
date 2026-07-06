"""Memory service abstractions for WalletMind ADK runtime.

Memory service is abstracted so long-term/persistent backends can be adopted
without changing runner/runtime wiring.
"""

from __future__ import annotations

import importlib
import logging
from typing import Any


class AdkMemoryImportError(ImportError):
    """Raised when ADK memory dependencies are unavailable."""


class WalletMindMemoryServiceFactory:
    """Factory for creating ADK memory services.

    Uses ADK in-memory memory storage for Sprint 1.1 while preserving a clean
    extension point for future persistent memory services.
    """

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger(__name__)

    def create(self) -> Any:
        """Create and return the configured ADK MemoryService instance."""

        service_cls = self._load_in_memory_memory_service()
        service = service_cls()
        self._logger.debug("Initialized ADK InMemoryMemoryService.")
        return service

    @staticmethod
    def _load_in_memory_memory_service() -> type[Any]:
        try:
            module = importlib.import_module("google.adk.memory")
            return getattr(module, "InMemoryMemoryService")
        except (ImportError, AttributeError) as exc:
            raise AdkMemoryImportError(
                "google-adk 2.x with InMemoryMemoryService is required. "
                "Install/upgrade with: pip install 'google-adk>=2.0'"
            ) from exc
