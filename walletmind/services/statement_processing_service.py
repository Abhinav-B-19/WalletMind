"""Statement processing pipeline service for statement classification."""

from __future__ import annotations

from datetime import datetime, timezone
import logging
from pathlib import Path
from time import perf_counter
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from backend.app.models.statement import Statement, StatementStatus
from walletmind.exceptions import StatementNotFoundError, StatementStorageError
from walletmind.services.statement_classifier import (
    BankDetector,
    FileInspector,
    ParserResolver,
    StatementClassifier,
)

logger = logging.getLogger(__name__)


class StatementProcessingService:
    """Coordinates statement classification status transitions without transaction parsing."""

    def __init__(self, *, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory
        self._classifier = StatementClassifier(
            file_inspector=FileInspector(),
            bank_detector=BankDetector(),
            parser_resolver=ParserResolver(),
        )

    def process_statement(
        self,
        *,
        statement_uuid: UUID | str,
        original_filename: str,
        stored_file_path: str,
        content_type: str | None = None,
    ) -> None:
        """Run classification pipeline: uploaded -> classifying -> classified -> ready_for_parsing."""

        parsed_uuid = self._coerce_uuid(statement_uuid)
        started_at = datetime.now(tz=timezone.utc)
        pipeline_started = perf_counter()

        try:
            with self._session_factory() as session:
                statement = self._get_statement(session, parsed_uuid)
                statement.status = StatementStatus.UPLOADED
                statement.processing_started_at = started_at
                statement.processing_error = None
                session.commit()
                logger.info(
                    "Upload acknowledged for classification",
                    extra={
                        "statement_uuid": statement.uuid,
                        "status": statement.status.value,
                    },
                )

            with self._session_factory() as session:
                statement = self._get_statement(session, parsed_uuid)
                statement.status = StatementStatus.CLASSIFYING
                session.commit()

            file_bytes = Path(stored_file_path).read_bytes()
            classification_result = self._classifier.classify(
                original_filename=original_filename,
                file_bytes=file_bytes,
                content_type=content_type,
            )

            with self._session_factory() as session:
                statement = self._get_statement(session, parsed_uuid)
                statement.bank_name = classification_result.detected_bank
                statement.detected_file_type = classification_result.detected_file_type
                statement.parser_type = classification_result.parser_type
                statement.classification_confidence = classification_result.confidence
                statement.classification_method = classification_result.classification_method
                statement.classified_at = datetime.now(tz=timezone.utc)
                statement.status = StatementStatus.CLASSIFIED
                session.commit()

                statement.status = StatementStatus.READY_FOR_PARSING
                statement.processing_completed_at = datetime.now(tz=timezone.utc)
                session.commit()
                logger.info(
                    "Statement classified",
                    extra={
                        "statement_uuid": statement.uuid,
                        "detected_bank": statement.bank_name,
                        "detection_rule": statement.classification_method,
                        "classification_confidence": statement.classification_confidence,
                        "selected_parser": statement.parser_type,
                        "classification_duration_ms": int(
                            (perf_counter() - pipeline_started) * 1000
                        ),
                        "unknown_reason": classification_result.unknown_reason,
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
    def _get_statement(session: Session, statement_uuid: UUID) -> Statement:
        statement = session.scalar(select(Statement).where(Statement.uuid == str(statement_uuid)))
        if statement is None:
            raise StatementNotFoundError(f"Statement '{statement_uuid}' was not found")
        return statement
