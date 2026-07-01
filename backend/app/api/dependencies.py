"""Dependency providers for API routes."""

from __future__ import annotations

from fastapi import Request

from walletmind.services.user_service import UserService


def get_user_service(request: Request) -> UserService:
    """Return the app-scoped user service instance."""

    return request.app.state.user_service
