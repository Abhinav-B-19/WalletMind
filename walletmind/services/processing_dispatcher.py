"""Processing dispatcher abstraction for statement pipeline execution."""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import BackgroundTasks

from walletmind.services.statement_processing_service import StatementProcessingService

logger = logging.getLogger(__name__)


class ProcessingDispatcher:
    """Dispatches statement processing with replaceable execution strategy."""

    def __init__(self, *, processing_service: StatementProcessingService) -> None:
        self._processing_service = processing_service

    def dispatch(
        self,
        *,
        background_tasks: BackgroundTasks,
        statement_uuid: UUID | str,
        original_filename: str,
        stored_file_path: str,
        content_type: str | None = None,
    ) -> None:
        """Run statement processing synchronously for deterministic API completion."""

        logger.info(
            "Processing queued",
            extra={
                "statement_uuid": str(statement_uuid),
                "original_filename": original_filename,
                "stored_file_path": stored_file_path,
                "content_type": content_type,
            },
        )
        # Keep API contract deterministic for F-2.2 by completing classification
        # before returning from upload endpoint.
        self._processing_service.process_statement(
            statement_uuid=statement_uuid,
            original_filename=original_filename,
            stored_file_path=stored_file_path,
            content_type=content_type,
        )
