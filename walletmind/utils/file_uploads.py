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
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
}

EXTENSION_TO_DETECTED_FILE_TYPE: dict[str, str] = {
    ".csv": "csv",
    ".xls": "xls",
    ".xlsx": "xlsx",
    ".pdf": "pdf",
    ".png": "png",
    ".jpg": "jpg",
    ".jpeg": "jpeg",
}

MIME_TO_DETECTED_FILE_TYPE: dict[str, str] = {
    "text/csv": "csv",
    "application/csv": "csv",
    "application/vnd.ms-excel": "xls",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
    "application/pdf": "pdf",
    "image/png": "png",
    "image/jpg": "jpg",
    "image/jpeg": "jpeg",
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


def detect_file_type(*, extension: str, content_type: str | None = None) -> str:
    """Detect normalized file type by extension, then optional MIME type, else unknown."""

    normalized = extension.lower()
    if normalized in EXTENSION_TO_DETECTED_FILE_TYPE:
        return EXTENSION_TO_DETECTED_FILE_TYPE[normalized]

    if content_type:
        mime = content_type.strip().lower()
        if mime in MIME_TO_DETECTED_FILE_TYPE:
            return MIME_TO_DETECTED_FILE_TYPE[mime]

    return "unknown"


def generate_stored_filename(extension: str) -> str:
    """Generate a UUID-based stored filename preserving extension."""

    return f"{uuid4()}{extension}"