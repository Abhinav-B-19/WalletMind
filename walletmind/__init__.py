"""WalletMind package entrypoint.

WalletMind is currently in package bootstrap mode. The public exports here are
limited to stable package identity metadata.
"""

from walletmind.version import (
    APP_NAME,
    APP_TAGLINE,
    AUTHOR,
    LICENSE,
    PROJECT_DESCRIPTION,
    PYTHON_REQUIRES,
    STATUS,
    VERSION,
    __version__,
)

__all__ = [
    "APP_NAME",
    "APP_TAGLINE",
    "AUTHOR",
    "LICENSE",
    "PROJECT_DESCRIPTION",
    "PYTHON_REQUIRES",
    "STATUS",
    "VERSION",
    "__version__",
]