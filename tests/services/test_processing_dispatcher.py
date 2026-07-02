"""Unit tests for processing dispatcher behavior."""

from __future__ import annotations

from fastapi import BackgroundTasks

from walletmind.services.processing_dispatcher import ProcessingDispatcher


class _RecordingProcessingService:
    def __init__(self) -> None:
        self.calls: list[dict[str, str | None]] = []

    def process_statement(
        self,
        *,
        statement_uuid: str,
        original_filename: str,
        content_type: str | None = None,
    ) -> None:
        self.calls.append(
            {
                "statement_uuid": statement_uuid,
                "original_filename": original_filename,
                "content_type": content_type,
            }
        )


def test_dispatcher_adds_background_task_and_invokes_processing() -> None:
    service = _RecordingProcessingService()
    dispatcher = ProcessingDispatcher(processing_service=service)
    background_tasks = BackgroundTasks()

    dispatcher.dispatch(
        background_tasks=background_tasks,
        statement_uuid="8fe70b89-2325-42b6-82a6-16c6268d56eb",
        original_filename="statement.csv",
        content_type="text/csv",
    )

    assert len(background_tasks.tasks) == 1

    # Execute queued tasks to validate invocation payload.
    for task in background_tasks.tasks:
        task.func(*task.args, **task.kwargs)

    assert service.calls == [
        {
            "statement_uuid": "8fe70b89-2325-42b6-82a6-16c6268d56eb",
            "original_filename": "statement.csv",
            "content_type": "text/csv",
        }
    ]
