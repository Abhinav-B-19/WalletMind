"""Transaction model for parsed statement rows."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import Date, DateTime, ForeignKey, Index, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database.base import Base

if TYPE_CHECKING:
    from backend.app.models.statement import Statement


class Transaction(Base):
    """Represents a normalized transaction parsed from a statement."""

    __tablename__ = "transactions"
    __table_args__ = (
        UniqueConstraint(
            "statement_id",
            "transaction_date",
            "description",
            "amount",
            name="uq_transactions_statement_date_desc_amount",
        ),
        Index("ix_transactions_statement_id_date", "statement_id", "transaction_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(
        String(36),
        default=lambda: str(uuid4()),
        unique=True,
        index=True,
        nullable=False,
    )
    statement_id: Mapped[int] = mapped_column(
        ForeignKey("statements.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    transaction_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    debit: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    credit: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), index=True, nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(16), nullable=False)
    balance: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    reference_number: Mapped[str | None] = mapped_column(String(120), nullable=True)
    raw_row_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    statement: Mapped["Statement"] = relationship(back_populates="transactions")
