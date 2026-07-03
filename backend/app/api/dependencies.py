"""Dependency providers for API routes."""

from __future__ import annotations

from fastapi import Request

from backend.app.services.ai.ai_service import AIService
from backend.app.services.analysis.spending_insights_service import (
    SpendingInsightsService,
)
from backend.app.services.assistant.financial_assistant_service import (
    FinancialAssistantService,
)
from backend.app.services.health.financial_health_service import (
    FinancialHealthService,
)
from walletmind.services.processing_dispatcher import ProcessingDispatcher
from walletmind.services.statement_upload_service import StatementUploadService
from walletmind.services.transaction_service import TransactionService
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


def get_transaction_service(request: Request) -> TransactionService:
    """Return the app-scoped transaction service instance."""

    return request.app.state.transaction_service


def get_ai_service(request: Request) -> AIService:
    """Return the app-scoped AI service instance."""

    return request.app.state.ai_service


def get_spending_insights_service(request: Request) -> SpendingInsightsService:
    """Return the app-scoped spending insights service instance."""

    return request.app.state.spending_insights_service


def get_financial_assistant_service(request: Request) -> FinancialAssistantService:
    """Return the app-scoped financial assistant service instance."""

    return request.app.state.financial_assistant_service


def get_financial_health_service(request: Request) -> FinancialHealthService:
    """Return the app-scoped financial health service instance."""

    return request.app.state.financial_health_service
