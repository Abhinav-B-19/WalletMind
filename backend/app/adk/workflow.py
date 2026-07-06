"""Base ADK workflow skeleton for WalletMind.

This file introduces only the runtime workflow foundation. It intentionally
contains no financial agents, no routing logic, and no business computation.
"""

from __future__ import annotations

import importlib
import logging
from typing import Any

from backend.app.adk.config import AdkRuntimeSettings

# Documented future topology order for Sprint 1.2+.
FUTURE_NODE_SEQUENCE = ["planner", "health", "budget", "insights", "report", "assistant"]


class AdkWorkflowImportError(ImportError):
    """Raised when ADK workflow dependencies are unavailable."""


class WalletMindWorkflowFactory:
    """Factory that builds WalletMind's root workflow skeleton."""

    def __init__(
        self,
        settings: AdkRuntimeSettings,
        logger: logging.Logger | None = None,
    ) -> None:
        self._settings = settings
        self._logger = logger or logging.getLogger(__name__)

    def create(self) -> Any:
        """Create the base Workflow with a bootstrap node only.

        The bootstrap node exists to produce a valid ADK Workflow graph while
        preserving a zero-business-logic foundation for future agent nodes.
        """

        workflow_cls = self._load_workflow_class()
        node_decorator = self._load_node_decorator()

        @node_decorator(name="walletmind_bootstrap")
        def walletmind_bootstrap(node_input: Any) -> Any:
            return node_input

        workflow = workflow_cls(
            name=self._settings.root_workflow_name,
            edges=[("START", walletmind_bootstrap)],
        )
        self._logger.debug(
            "Initialized base ADK workflow skeleton.",
            extra={"future_nodes": list(FUTURE_NODE_SEQUENCE)},
        )
        return workflow

    @staticmethod
    def _load_workflow_class() -> type[Any]:
        try:
            module = importlib.import_module("google.adk")
            return getattr(module, "Workflow")
        except (ImportError, AttributeError) as exc:
            raise AdkWorkflowImportError(
                "google-adk 2.x with Workflow is required. "
                "Install/upgrade with: pip install 'google-adk>=2.0'"
            ) from exc

    @staticmethod
    def _load_node_decorator() -> Any:
        try:
            module = importlib.import_module("google.adk.workflow")
            return getattr(module, "node")
        except (ImportError, AttributeError) as exc:
            raise AdkWorkflowImportError(
                "google-adk 2.x workflow.node is required. "
                "Install/upgrade with: pip install 'google-adk>=2.0'"
            ) from exc
