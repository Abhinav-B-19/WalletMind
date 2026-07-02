"""Dependency providers for API routes."""

from __future__ import annotations

from fastapi import Request

from walletmind.services.processing_dispatcher import ProcessingDispatcher
from walletmind.services.statement_upload_service import StatementUploadService
from walletmind.services.user_service import UserService


def get_user_service(request: Request) -> UserService:
    """Return the app-scoped user service instance."""

    return request.app.state.user_service


def get_statement_upload_service(request: Request) -> StatementUploadService:
    """Return the app-scoped statement upload service instance."""

    return request.app.state.statement_upload_service


def get_processing_dispatcher(request: Request) -> ProcessingDispatcher:
    """Return the app-scoped statement processing dispatcher instance."""

    return request.app.state.processing_dispatcher
