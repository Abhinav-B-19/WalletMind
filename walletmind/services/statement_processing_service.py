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
from walletmind.services.statement_parsers import ParserFactory, ParserRegistry
from walletmind.services.statement_classifier import (
    BankDetector,
    FileInspector,
    ParserResolver,
    StatementClassifier,
)
from walletmind.services.transaction_service import TransactionService

logger = logging.getLogger(__name__)
parser_logger = logging.getLogger("walletmind.parsers")


class StatementProcessingService:
    """Coordinates statement classification and transaction parsing status transitions."""

    def __init__(self, *, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory
        self._classifier = StatementClassifier(
            file_inspector=FileInspector(),
            bank_detector=BankDetector(),
            parser_resolver=ParserResolver(),
        )
        self._parser_factory = ParserFactory(registry=ParserRegistry())
        self._transaction_service = TransactionService(session_factory=session_factory)

    def process_statement(
        self,
        *,
        statement_uuid: UUID | str,
        original_filename: str,
        stored_file_path: str,
        content_type: str | None = None,
    ) -> None:
        """Run classification and parsing pipeline until ready_for_analysis."""

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

            try:
                parser_result, parser_metrics = self._parser_factory.execute(
                    parser_name=classification_result.parser_type,
                    content=file_bytes,
                    filename=original_filename,
                    content_type=content_type,
                )

                inserted_count, duplicate_count = self._transaction_service.store_transactions(
                    statement_uuid=parsed_uuid,
                    transactions=parser_result.transactions,
                )

                parser_logger.info(
                    "Transactions stored",
                    extra={
                        "statement_uuid": str(parsed_uuid),
                        "transactions_extracted": len(parser_result.transactions),
                        "transactions_stored": inserted_count,
                        "duplicates_skipped": duplicate_count,
                    },
                )
            except Exception as exc:  # noqa: BLE001
                self._mark_parse_failed(parsed_uuid, str(exc))
                raise

            with self._session_factory() as session:
                statement = self._get_statement(session, parsed_uuid)
                statement.parsed_transaction_count = inserted_count
                statement.failed_transaction_count = parser_result.rows_skipped
                statement.rows_read = parser_result.rows_read
                statement.rows_parsed = parser_result.rows_parsed
                statement.rows_skipped = parser_result.rows_skipped
                statement.parsing_duration_ms = parser_metrics.duration_ms
                statement.parsed_at = datetime.now(tz=timezone.utc)
                statement.processing_completed_at = datetime.now(tz=timezone.utc)

                if inserted_count > 0:
                    statement.status = StatementStatus.READY_FOR_ANALYSIS
                    statement.processing_error = None
                else:
                    statement.status = StatementStatus.PARSE_FAILED
                    parser_error = (
                        "Transaction parsing produced zero transactions. "
                        f"Rows scanned={parser_result.rows_scanned}, rows skipped={parser_result.rows_skipped}."
                    )
                    if parser_result.errors:
                        parser_error = f"{parser_error} Errors: {', '.join(parser_result.errors[:3])}"
                    statement.processing_error = parser_error[:500]

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
                        "parser_selected": parser_result.parser_name,
                        "rows_scanned": parser_result.rows_scanned,
                        "rows_skipped": parser_result.rows_skipped,
                        "transactions_extracted": inserted_count,
                        "duplicates_skipped": duplicate_count,
                        "parser_duration_ms": parser_metrics.duration_ms,
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
            with self._session_factory() as session:
                statement = self._get_statement(session, parsed_uuid)
                if statement.status != StatementStatus.PARSE_FAILED:
                    self._mark_failed(parsed_uuid, str(exc))
            raise

    def _mark_failed(self, statement_uuid: UUID, error_message: str) -> None:
        with self._session_factory() as session:
            statement = self._get_statement(session, statement_uuid)
            statement.status = StatementStatus.FAILED
            statement.processing_completed_at = datetime.now(tz=timezone.utc)
            statement.processing_error = error_message[:500]
            session.commit()

    def _mark_parse_failed(self, statement_uuid: UUID, error_message: str) -> None:
        with self._session_factory() as session:
            statement = self._get_statement(session, statement_uuid)
            statement.status = StatementStatus.PARSE_FAILED
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
