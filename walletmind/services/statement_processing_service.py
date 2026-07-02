"""Statement processing pipeline service for file type detection and parser selection."""

from __future__ import annotations

from datetime import datetime, timezone
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from backend.app.models.statement import Statement, StatementStatus
from walletmind.exceptions import StatementNotFoundError, StatementStorageError
from walletmind.utils.file_uploads import detect_file_type, parser_type_for_extension

logger = logging.getLogger(__name__)


class StatementProcessingService:
    """Coordinates statement preprocessing status transitions without parsing."""

    def __init__(self, *, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def process_statement(
        self,
        *,
        statement_uuid: UUID | str,
        original_filename: str,
        content_type: str | None = None,
    ) -> None:
        """Run preprocessing pipeline: processing -> detect/parser -> ready_for_parsing."""

        parsed_uuid = self._coerce_uuid(statement_uuid)
        started_at = datetime.now(tz=timezone.utc)

        try:
            with self._session_factory() as session:
                statement = self._get_statement(session, parsed_uuid)
                statement.status = StatementStatus.PROCESSING
                statement.processing_started_at = started_at
                statement.processing_error = None
                session.commit()
                logger.info(
                    "Processing started",
                    extra={
                        "statement_uuid": statement.uuid,
                        "status": statement.status.value,
                    },
                )

            detected_file_type = detect_file_type(
                extension=f".{self._normalize_file_type_from_name(original_filename)}",
                content_type=content_type,
            )
            logger.info(
                "File type detected",
                extra={
                    "statement_uuid": str(parsed_uuid),
                    "detected_file_type": detected_file_type,
                },
            )
            parser_type = parser_type_for_extension(f".{detected_file_type}") or "unknown"
            logger.info(
                "Parser selected",
                extra={
                    "statement_uuid": str(parsed_uuid),
                    "parser_type": parser_type,
                },
            )

            with self._session_factory() as session:
                statement = self._get_statement(session, parsed_uuid)
                statement.detected_file_type = detected_file_type
                statement.parser_type = parser_type
                statement.status = StatementStatus.READY_FOR_PARSING
                statement.processing_completed_at = datetime.now(tz=timezone.utc)
                session.commit()
                logger.info(
                    "Processing completed",
                    extra={
                        "statement_uuid": statement.uuid,
                        "status": statement.status.value,
                    },
                )
        except StatementNotFoundError:
            raise
        except SQLAlchemyError as exc:
            self._mark_failed(parsed_uuid, str(exc))
            raise StatementStorageError("Failed to process statement metadata") from exc
        except Exception as exc:
            self._mark_failed(parsed_uuid, str(exc))
            raise

    def _mark_failed(self, statement_uuid: UUID, error_message: str) -> None:
        with self._session_factory() as session:
            statement = self._get_statement(session, statement_uuid)
            statement.status = StatementStatus.FAILED
            statement.processing_completed_at = datetime.now(tz=timezone.utc)
            statement.processing_error = error_message[:500]
            session.commit()

    @staticmethod
    def _coerce_uuid(value: UUID | str) -> UUID:
        if isinstance(value, UUID):
            return value
        return UUID(str(value))

    @staticmethod
    def _normalize_file_type_from_name(filename: str) -> str:
        # Preserve existing service behavior where file_type stores extension without dot.
        suffix = filename.rsplit(".", maxsplit=1)
        return suffix[-1].lower() if len(suffix) == 2 else ""

    @staticmethod
    def _get_statement(session: Session, statement_uuid: UUID) -> Statement:
        statement = session.scalar(select(Statement).where(Statement.uuid == str(statement_uuid)))
        if statement is None:
            raise StatementNotFoundError(f"Statement '{statement_uuid}' was not found")
        return statement
