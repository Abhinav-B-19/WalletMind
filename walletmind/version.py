"""Package metadata for WalletMind.

This module is the single source of truth for package identity metadata used by
both imports and the lightweight command-line entrypoint.
"""

from typing import Final

APP_NAME: Final[str] = "WalletMind"
APP_TAGLINE: Final[str] = "AI Financial Concierge"
PROJECT_DESCRIPTION: Final[str] = "Google Kaggle AI Agents Capstone Project"
AUTHOR: Final[str] = "WalletMind Contributors"
LICENSE: Final[str] = "MIT"
PYTHON_REQUIRES: Final[str] = ">=3.12"
PYTHON_DISPLAY_VERSION: Final[str] = "3.12+"
STATUS: Final[str] = "Development"
VERSION: Final[str] = "0.1.0"

__version__: Final[str] = VERSION