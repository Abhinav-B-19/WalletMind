"""Core configuration values for the WalletMind backend."""

from pathlib import Path
from typing import Final

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[3]
STORAGE_DIR: Final[Path] = PROJECT_ROOT / "storage"
DATABASE_DIR: Final[Path] = STORAGE_DIR / "database"
DATABASE_FILE: Final[Path] = DATABASE_DIR / "walletmind.db"
DATABASE_URL: Final[str] = f"sqlite:///{DATABASE_FILE.as_posix()}"
SQLITE_CONNECT_ARGS: Final[dict[str, bool]] = {"check_same_thread": False}