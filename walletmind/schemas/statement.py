"""Pydantic schemas for statement persistence and transfer objects."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class StatementStatus(str, Enum):
    """Supported statement processing states."""

    QUEUED = "queued"
    UPLOADED = "uploaded"
    CLASSIFYING = "classifying"
    CLASSIFIED = "classified"
    PROCESSING = "processing"
    READY_FOR_PARSING = "ready_for_parsing"
    PARSED = "parsed"
    ANALYSIS_PENDING = "analysis_pending"
    READY_FOR_ANALYSIS = "ready_for_analysis"
    PARSE_FAILED = "parse_failed"
    COMPLETED = "completed"
    FAILED = "failed"


class StatementBase(BaseModel):
    """Common statement fields shared across request and response schemas."""

    user_id: int = Field(gt=0)
    original_filename: str = Field(min_length=1, max_length=255)
    stored_filename: str = Field(min_length=1, max_length=255)
    bank_name: Optional[str] = Field(default=None, max_length=120)
    file_type: str = Field(min_length=1, max_length=32)
    file_size: int = Field(gt=0)
    status: StatementStatus = StatementStatus.UPLOADED


class StatementCreate(StatementBase):
    """Schema for creating a persisted statement record."""


class StatementUpdate(BaseModel):
    """Schema for updating mutable statement fields."""

    original_filename: Optional[str] = Field(default=None, min_length=1, max_length=255)
    stored_filename: Optional[str] = Field(default=None, min_length=1, max_length=255)
    bank_name: Optional[str] = Field(default=None, max_length=120)
    file_type: Optional[str] = Field(default=None, min_length=1, max_length=32)
    file_size: Optional[int] = Field(default=None, gt=0)
    status: Optional[StatementStatus] = None


class StatementStatusUpdate(BaseModel):
    """Schema for updating statement processing status."""

    status: StatementStatus


class StatementRead(StatementBase):
    """Schema for returning persisted statement records."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    uuid: UUID
    uploaded_at: datetime
    updated_at: datetime


class UploadResponseDTO(BaseModel):
    """API/service response payload for uploaded statement metadata."""

    statement_uuid: UUID
    stored_file_path: str | None = None
    original_filename: str
    stored_filename: str
    file_size: int
    file_type: str
    parser_type: str
    bank_name: Optional[str] = None
    classification_confidence: float | None = None
    classification_method: str | None = None
    classified_at: datetime | None = None
    parsed_transaction_count: int = 0
    failed_transaction_count: int = 0
    parsed_at: datetime | None = None
    analysis_status: StatementStatus
    status: StatementStatus
    uploaded_at: datetime
