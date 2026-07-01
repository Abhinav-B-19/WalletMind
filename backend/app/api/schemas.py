"""API-level response schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standardized error response payload."""

    code: str = Field(..., description="Stable error identifier")
    message: str = Field(..., description="Human-readable error message")
    details: Any | None = Field(default=None, description="Optional error details")
