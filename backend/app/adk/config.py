"""Configuration primitives for WalletMind ADK runtime wiring.

This module intentionally contains only runtime-level settings. It does not
contain financial logic and should remain stable as agent capabilities evolve.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AdkRuntimeSettings:
    """Settings required to bootstrap WalletMind's ADK runtime foundation.

    These values are sourced from environment variables to stay compatible with
    existing deployment/configuration practices without changing current APIs.
    """

    app_name: str = "walletmind"
    root_workflow_name: str = "walletmind_root_workflow"
    default_user_id: str = "walletmind-system"
    default_session_prefix: str = "wm-session"
    model_name: str = "gemini-2.5-flash"

    @classmethod
    def from_environment(cls) -> "AdkRuntimeSettings":
        """Build runtime settings from process environment variables."""

        return cls(
            app_name=os.getenv("WALLETMIND_ADK_APP_NAME", "walletmind"),
            root_workflow_name=os.getenv(
                "WALLETMIND_ADK_WORKFLOW_NAME", "walletmind_root_workflow"
            ),
            default_user_id=os.getenv("WALLETMIND_ADK_DEFAULT_USER", "walletmind-system"),
            default_session_prefix=os.getenv(
                "WALLETMIND_ADK_SESSION_PREFIX", "wm-session"
            ),
            # Reuse existing model configuration source for future agent nodes.
            model_name=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        )
