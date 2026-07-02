"""Statement model for uploaded bank statement persistence."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database.base import Base

if TYPE_CHECKING:
    from backend.app.models.user import User


class StatementStatus(str, Enum):
    """Supported lifecycle states for uploaded statements."""

    QUEUED = "queued"
    UPLOADED = "uploaded"
    CLASSIFYING = "classifying"
    CLASSIFIED = "classified"
    PROCESSING = "processing"
    READY_FOR_PARSING = "ready_for_parsing"
    PARSED = "parsed"
    ANALYSIS_PENDING = "analysis_pending"
    COMPLETED = "completed"
    FAILED = "failed"


class Statement(Base):
    """Represents an uploaded bank statement file."""

    __tablename__ = "statements"
    __table_args__ = (
        Index("ix_statements_user_id_status", "user_id", "status"),
        Index("ix_statements_user_id_uploaded_at", "user_id", "uploaded_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(
        String(36),
        default=lambda: str(uuid4()),
        unique=True,
        index=True,
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    bank_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    file_type: Mapped[str] = mapped_column(String(32), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    detected_file_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    parser_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    classification_confidence: Mapped[float | None] = mapped_column(nullable=True)
    classification_method: Mapped[str | None] = mapped_column(String(120), nullable=True)
    classified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    status: Mapped[StatementStatus] = mapped_column(
        SAEnum(StatementStatus, native_enum=False),
        default=StatementStatus.UPLOADED,
        index=True,
        nullable=False,
    )
    processing_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    processing_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    processing_error: Mapped[str | None] = mapped_column(String(500), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="statements")
