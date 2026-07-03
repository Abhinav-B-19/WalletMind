"""Core configuration values for the WalletMind backend."""

from functools import lru_cache
from pathlib import Path
from typing import Final

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[3]
STORAGE_DIR: Final[Path] = PROJECT_ROOT / "storage"
DATABASE_DIR: Final[Path] = STORAGE_DIR / "database"
DATABASE_FILE: Final[Path] = DATABASE_DIR / "walletmind.db"
DATABASE_URL: Final[str] = f"sqlite:///{DATABASE_FILE.as_posix()}"
SQLITE_CONNECT_ARGS: Final[dict[str, bool]] = {"check_same_thread": False}


class SettingsLoadError(Exception):
    """Raised when AI settings are invalid or missing."""


class AISettings(BaseSettings):
    """Validated AI configuration loaded from environment variables."""

    gemini_api_key: str = Field(..., min_length=1)
    gemini_model: str = Field(default="gemini-2.5-flash", min_length=1)
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    max_output_tokens: int = Field(default=1024, ge=1)

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_ai_settings() -> AISettings:
    """
    Load and validate AI configuration.

    Raises:
        SettingsLoadError: If the configuration is invalid or missing.
    """
    try:
        return AISettings()
    except Exception as exc:
        raise SettingsLoadError(
            "Invalid or missing Gemini AI configuration."
        ) from exc