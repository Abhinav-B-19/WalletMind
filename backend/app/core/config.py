"""Core configuration values for the WalletMind backend."""

from pathlib import Path
from typing import Final

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[3]
STORAGE_DIR: Final[Path] = PROJECT_ROOT / "storage"
DATABASE_DIR: Final[Path] = STORAGE_DIR / "database"
DATABASE_FILE: Final[Path] = DATABASE_DIR / "walletmind.db"
SQLITE_CONNECT_ARGS: Final[dict[str, bool]] = {"check_same_thread": False}


class SettingsLoadError(Exception):
    """Raised when AI settings are invalid or missing."""


class AppSettings(BaseSettings):
    """Validated application configuration loaded from environment variables."""

    database_url: str = Field(default=f"sqlite:///{DATABASE_FILE.as_posix()}")
    allowed_origins: str = Field(default="http://localhost:5173")

    gemini_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("GEMINI_API_KEY", "GOOGLE_API_KEY"),
    )
    gemini_model: str = Field(default="gemini-2.5-flash", min_length=1)
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    max_output_tokens: int = Field(default=1024, ge=1)
    developer_mode: bool = Field(default=False)

    session_secret_key: str = Field(
        default="walletmind-dev-session-secret-change-me",
        min_length=16,
    )
    session_cookie_name: str = Field(default="walletmind_session", min_length=1)
    session_max_age_seconds: int = Field(default=8 * 60 * 60, ge=300)
    session_cookie_secure: bool = Field(default=False)

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


def _parse_allowed_origins(value: str) -> list[str]:
    """Parse comma-separated origins and normalize whitespace/trailing slashes."""

    origins = [origin.strip().rstrip("/") for origin in value.split(",")]
    return [origin for origin in origins if origin]


try:
    settings = AppSettings()
except Exception as exc:
    raise SettingsLoadError("Invalid or missing application configuration.") from exc

DATABASE_URL: Final[str] = settings.database_url
ALLOWED_ORIGINS: Final[list[str]] = _parse_allowed_origins(settings.allowed_origins)


def get_ai_settings() -> AppSettings:
    """
    Load and validate AI configuration.

    Raises:
        SettingsLoadError: If the configuration is invalid or missing.
    """
    try:
        return settings
    except Exception as exc:
        raise SettingsLoadError(
            "Invalid or missing Gemini AI configuration."
        ) from exc