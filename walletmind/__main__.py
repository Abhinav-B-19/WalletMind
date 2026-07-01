"""Command-line entrypoint for the WalletMind package bootstrap."""

from walletmind.version import (
    APP_NAME,
    APP_TAGLINE,
    PROJECT_DESCRIPTION,
    PYTHON_DISPLAY_VERSION,
    STATUS,
    VERSION,
)

BANNER_WIDTH = 52
NEXT_STEP = "Open notebook/WalletMind.ipynb"


def build_banner() -> str:
    """Build the WalletMind startup banner.

    Returns:
        A formatted startup banner for the package bootstrap CLI.
    """
    border = "=" * BANNER_WIDTH
    lines = [
        border,
        APP_NAME,
        APP_TAGLINE,
        PROJECT_DESCRIPTION,
        "",
        f"Version : {VERSION}",
        f"Python  : {PYTHON_DISPLAY_VERSION}",
        f"Status  : {STATUS}",
        "",
        "Repository initialized successfully.",
        "",
        "Next Step:",
        NEXT_STEP,
        border,
    ]
    return "\n".join(lines)


def main() -> int:
    """Run the lightweight WalletMind startup command.

    Returns:
        Process exit code. Returns zero when the banner is displayed.
    """
    print(build_banner())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())