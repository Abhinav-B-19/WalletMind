"""Helpers for statement upload file naming and extension handling."""

from __future__ import annotations

import re
from pathlib import Path
from uuid import uuid4


EXTENSION_TO_PARSER_TYPE: dict[str, str] = {
    ".csv": "csv",
    ".xls": "excel",
    ".xlsx": "excel",
    ".pdf": "pdf",
}


def normalized_extension(filename: str) -> str:
    """Return the normalized lowercase suffix for a filename."""

    return Path(filename).suffix.lower()


def sanitize_filename(filename: str) -> str:
    """Normalize a user-provided filename to a safe basename."""

    basename = Path(filename).name.strip()
    sanitized = re.sub(r"[^A-Za-z0-9._-]", "_", basename)
    sanitized = sanitized.strip("._")
    return sanitized


def parser_type_for_extension(extension: str) -> str | None:
    """Return parser type for a supported extension."""

    return EXTENSION_TO_PARSER_TYPE.get(extension.lower())


def generate_stored_filename(extension: str) -> str:
    """Generate a UUID-based stored filename preserving extension."""

    return f"{uuid4()}{extension}"