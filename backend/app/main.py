"""Backend entry point for WalletMind database initialization."""

import sys
from pathlib import Path


def _ensure_project_root_on_path() -> None:
    """Add the project root to Python's import path for direct script execution."""
    project_root = Path(__file__).resolve().parents[2]
    project_root_path = str(project_root)
    if project_root_path not in sys.path:
        sys.path.insert(0, project_root_path)


def main() -> int:
    """Initialize the WalletMind SQLite database.

    Returns:
        Process exit code. Returns zero when initialization succeeds.
    """
    _ensure_project_root_on_path()

    from backend.app.database.init_db import init_database

    print("Initializing WalletMind Database...")
    init_database()
    print("Connected to SQLite")
    print("Created tables")
    print("Database ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
