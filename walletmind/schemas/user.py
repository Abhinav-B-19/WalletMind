"""Pydantic schemas for user service input and output."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserCreateDTO(BaseModel):
    """Payload required to create a user."""

    name: str = Field(..., min_length=1)
    occupation: str = Field(..., min_length=1)
    monthly_income: float

    @field_validator("name", "occupation")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("field is required")
        return cleaned

    @field_validator("monthly_income")
    @classmethod
    def validate_monthly_income(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("monthly_income must be greater than 0")
        return value


class UserUpdateDTO(BaseModel):
    """Payload used to update user fields."""

    name: str | None = Field(default=None, min_length=1)
    occupation: str | None = Field(default=None, min_length=1)
    monthly_income: float | None = None

    @field_validator("name", "occupation")
    @classmethod
    def validate_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("field is required")
        return cleaned

    @field_validator("monthly_income")
    @classmethod
    def validate_optional_income(cls, value: float | None) -> float | None:
        if value is None:
            return value
        if value <= 0:
            raise ValueError("monthly_income must be greater than 0")
        return value


class UserDTO(BaseModel):
    """User data transfer object returned by the service layer."""

    model_config = ConfigDict(frozen=True)

    id: UUID
    name: str
    occupation: str
    monthly_income: float
