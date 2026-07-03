"""Exception handlers producing standardized API error responses."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from backend.app.services.ai.exceptions import (
    AIConfigurationError,
    AIRateLimitError,
    AIResponseError,
    AIServiceError,
)
from walletmind.exceptions import (
    DuplicateUserError,
    EmptyFileError,
    FileTooLargeError,
    NoTransactionsForStatementError,
    StatementInsightsError,
    StatementNotFoundError,
    StatementStorageError,
    UnsupportedFileTypeError,
    UserNotFoundError,
)


def register_error_handlers(app: FastAPI) -> None:
    """Attach shared exception handlers to the FastAPI app."""

    @app.exception_handler(UserNotFoundError)
    async def user_not_found_handler(
        request: Request, exc: UserNotFoundError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
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
                "success": False,
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
                "success": False,
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": jsonable_encoder(exc.errors()),
            },
        )

    @app.exception_handler(UnsupportedFileTypeError)
    async def unsupported_file_type_handler(
        request: Request, exc: UnsupportedFileTypeError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=415,
            content={
                "success": False,
                "code": "UNSUPPORTED_FILE_TYPE",
                "message": str(exc),
                "details": None,
            },
        )

    @app.exception_handler(EmptyFileError)
    async def empty_file_handler(request: Request, exc: EmptyFileError) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "code": "EMPTY_FILE",
                "message": str(exc),
                "details": None,
            },
        )

    @app.exception_handler(FileTooLargeError)
    async def file_too_large_handler(
        request: Request, exc: FileTooLargeError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=413,
            content={
                "success": False,
                "code": "FILE_TOO_LARGE",
                "message": str(exc),
                "details": None,
            },
        )

    @app.exception_handler(StatementNotFoundError)
    async def statement_not_found_handler(
        request: Request, exc: StatementNotFoundError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "code": "STATEMENT_NOT_FOUND",
                "message": str(exc),
                "details": None,
            },
        )

    @app.exception_handler(StatementStorageError)
    async def statement_storage_handler(
        request: Request, exc: StatementStorageError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "code": "STATEMENT_STORAGE_ERROR",
                "message": str(exc),
                "details": None,
            },
        )

    @app.exception_handler(NoTransactionsForStatementError)
    async def no_transactions_handler(
        request: Request, exc: NoTransactionsForStatementError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "code": "EMPTY_STATEMENT",
                "message": str(exc),
                "details": None,
            },
        )

    @app.exception_handler(AIConfigurationError)
    async def ai_configuration_handler(
        request: Request, exc: AIConfigurationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "code": "AI_CONFIGURATION_ERROR",
                "message": str(exc),
                "details": None,
            },
        )

    @app.exception_handler(AIRateLimitError)
    async def ai_rate_limit_handler(
        request: Request, exc: AIRateLimitError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=429,
            content={
                "success": False,
                "code": "AI_RATE_LIMIT",
                "message": str(exc),
                "details": None,
            },
        )

    @app.exception_handler(AIResponseError)
    async def ai_response_error_handler(
        request: Request, exc: AIResponseError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=502,
            content={
                "success": False,
                "code": "AI_RESPONSE_INVALID",
                "message": str(exc),
                "details": None,
            },
        )

    @app.exception_handler(AIServiceError)
    async def ai_service_error_handler(
        request: Request, exc: AIServiceError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=504,
            content={
                "success": False,
                "code": "AI_TIMEOUT_OR_SERVICE_ERROR",
                "message": str(exc),
                "details": None,
            },
        )

    @app.exception_handler(StatementInsightsError)
    async def statement_insights_handler(
        request: Request, exc: StatementInsightsError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "code": "STATEMENT_INSIGHTS_ERROR",
                "message": str(exc),
                "details": None,
            },
        )
