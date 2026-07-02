"""Shared API response envelope schemas."""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Standard success response envelope."""

    success: bool = Field(default=True, examples=[True])
    message: str = Field(..., description="Human-readable success message")
    data: T = Field(..., description="Payload for successful response")


class ApiErrorResponse(BaseModel):
    """Standard error response envelope."""

    success: bool = Field(default=False, examples=[False])
    code: str = Field(..., description="Stable error identifier")
    message: str = Field(..., description="Human-readable error message")
    details: Any | None = Field(default=None, description="Optional error details")


class DeleteStatusData(BaseModel):
    """Standard delete response payload."""

    statement_uuid: str
    status: str = Field(default="deleted")


class DeleteUserStatusData(BaseModel):
    """Standard delete response payload for user endpoints."""

    user_uuid: str
    status: str = Field(default="deleted")
