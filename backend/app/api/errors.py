"""Exception handlers producing standardized API error responses."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from walletmind.exceptions import DuplicateUserError, UserNotFoundError


def register_error_handlers(app: FastAPI) -> None:
    """Attach shared exception handlers to the FastAPI app."""

    @app.exception_handler(UserNotFoundError)
    async def user_not_found_handler(
        request: Request, exc: UserNotFoundError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={
                "code": "USER_NOT_FOUND",
                "message": str(exc),
                "details": None,
            },
        )

    @app.exception_handler(DuplicateUserError)
    async def duplicate_user_handler(
        request: Request, exc: DuplicateUserError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={
                "code": "DUPLICATE_USER",
                "message": str(exc),
                "details": None,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": jsonable_encoder(exc.errors()),
            },
        )
