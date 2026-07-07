"""Request-scoped context helpers for services that do not receive Request directly."""

from __future__ import annotations

from contextvars import ContextVar, Token

from fastapi import Request

_CURRENT_REQUEST: ContextVar[Request | None] = ContextVar(
    "walletmind_current_request",
    default=None,
)


def set_current_request(request: Request) -> Token[Request | None]:
    """Bind the current FastAPI request to a context variable."""

    return _CURRENT_REQUEST.set(request)


def reset_current_request(token: Token[Request | None]) -> None:
    """Reset request binding after middleware completion."""

    _CURRENT_REQUEST.reset(token)


def get_current_request() -> Request | None:
    """Return currently bound request if available."""

    return _CURRENT_REQUEST.get()
