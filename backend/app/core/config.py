"""Core configuration values for the WalletMind backend."""

import os
from pathlib import Path
from typing import Final

from pydantic import BaseModel, Field, ValidationError

from backend.app.services.ai.exceptions import AIConfigurationError

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[3]
STORAGE_DIR: Final[Path] = PROJECT_ROOT / "storage"
DATABASE_DIR: Final[Path] = STORAGE_DIR / "database"
DATABASE_FILE: Final[Path] = DATABASE_DIR / "walletmind.db"
DATABASE_URL: Final[str] = f"sqlite:///{DATABASE_FILE.as_posix()}"
SQLITE_CONNECT_ARGS: Final[dict[str, bool]] = {"check_same_thread": False}


class AISettings(BaseModel):
	"""Validated environment-backed settings for AI infrastructure."""

	gemini_api_key: str = Field(..., min_length=1)
	gemini_model: str = Field(default="gemini-1.5-flash", min_length=1)
	temperature: float = Field(default=0.2, ge=0.0, le=2.0)
	max_output_tokens: int = Field(default=1024, ge=1)


def get_ai_settings() -> AISettings:
	"""Load and validate AI settings from environment variables."""

	raw_api_key = os.getenv("GEMINI_API_KEY", "")
	raw_model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
	raw_temperature = os.getenv("TEMPERATURE", "0.2")
	raw_max_tokens = os.getenv("MAX_OUTPUT_TOKENS", "1024")

	if not raw_api_key.strip():
		raise AIConfigurationError("GEMINI_API_KEY is not configured.")

	try:
		return AISettings(
			gemini_api_key=raw_api_key.strip(),
			gemini_model=raw_model.strip(),
			temperature=float(raw_temperature),
			max_output_tokens=int(raw_max_tokens),
		)
	except ValidationError as exc:
		raise AIConfigurationError("Invalid AI configuration values.") from exc
	except (TypeError, ValueError) as exc:
		raise AIConfigurationError("Invalid AI configuration value type.") from exc