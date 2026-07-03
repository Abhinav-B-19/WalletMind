"""Transaction DTOs and parser result schemas."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TransactionDTO(BaseModel):
    """Normalized transaction payload returned by APIs and parsers."""

    transaction_uuid: UUID
    statement_uuid: UUID
    transaction_date: date
    description: str
    debit: Decimal | None = None
    credit: Decimal | None = None
    amount: Decimal
    transaction_type: str
    balance: Decimal | None = None
    currency: str | None = None
    reference_number: str | None = None
    raw_row_json: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class TransactionCreateDTO(BaseModel):
    """Internal DTO used by parsers before persistence."""

    transaction_date: date
    description: str
    debit: Decimal | None = None
    credit: Decimal | None = None
    amount: Decimal
    transaction_type: str
    balance: Decimal | None = None
    currency: str | None = None
    reference_number: str | None = None
    raw_row_json: dict[str, Any] = Field(default_factory=dict)


class ParserResultDTO(BaseModel):
    """Parser output with extraction and skip/failure metrics."""

    parser_name: str
    rows_read: int = 0
    rows_parsed: int = 0
    rows_scanned: int = 0
    rows_skipped: int = 0
    transactions: list[TransactionCreateDTO] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)


class TransactionReadDTO(BaseModel):
    """ORM-backed transaction read schema."""

    model_config = ConfigDict(from_attributes=True)

    transaction_uuid: UUID
    statement_uuid: UUID
    transaction_date: date
    description: str
    debit: Decimal | None = None
    credit: Decimal | None = None
    amount: Decimal
    transaction_type: str
    balance: Decimal | None = None
    currency: str | None = None
    reference_number: str | None = None
    raw_row_json: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
