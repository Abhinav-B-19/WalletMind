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
    merchant_name: str | None = None
    bank_gateway: str | None = None
    category: str
    raw_description: str
    clean_description: str
    normalized_transaction_type: str
    flags: dict[str, bool] = Field(default_factory=dict)
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
    merchant_name: str | None = None
    bank_gateway: str | None = None
    category: str = "Others"
    raw_description: str | None = None
    clean_description: str | None = None
    normalized_transaction_type: str = "other"
    is_internal_transfer: bool = False
    is_income: bool = False
    is_expense: bool = False
    raw_row_json: dict[str, Any] = Field(default_factory=dict)


class ParserResultDTO(BaseModel):
    """Parser output with extraction and skip/failure metrics."""

    parser_name: str
    rows_read: int = 0
    rows_parsed: int = 0
    rows_scanned: int = 0
    rows_skipped: int = 0
    direction_corrections: int = 0
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
    merchant_name: str | None = None
    bank_gateway: str | None = None
    category: str
    raw_description: str
    clean_description: str
    normalized_transaction_type: str
    flags: dict[str, bool] = Field(default_factory=dict)
    raw_row_json: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
