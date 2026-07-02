"""Helpers for statement upload file naming and extension handling."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4


def normalized_extension(filename: str) -> str:
    """Return the normalized lowercase suffix for a filename."""

    return Path(filename).suffix.lower()


def generate_stored_filename(extension: str) -> str:
    """Generate a UUID-based stored filename preserving extension."""

    return f"{uuid4()}{extension}"