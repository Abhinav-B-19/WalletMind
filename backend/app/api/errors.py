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
    AISessionExpiredError,
    AIServiceError,
    AIUserKeyInvalidError,
    AIUserKeyInvalidFormatError,
    AIUserKeyNetworkError,
    AIUserKeyPermissionDeniedError,
    AIUserKeyQuotaExceededError,
    AIUserKeySDKCompatibilityError,
    AIUserKeyUnsupportedAuthKeyError,
    AIUserKeyUnknownError,
)
from walletmind.exceptions import (
    AssistantNoDataError,
    AssistantValidationError,
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

    @app.exception_handler(AIUserKeyInvalidError)
    async def ai_user_key_invalid_handler(
        request: Request, exc: AIUserKeyInvalidError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "code": "AI_KEY_INVALID",
                "message": str(exc),
                "details": None,
            },
        )

    @app.exception_handler(AIUserKeyInvalidFormatError)
    async def ai_user_key_invalid_format_handler(
        request: Request, exc: AIUserKeyInvalidFormatError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "code": "AI_KEY_INVALID_FORMAT",
                "message": str(exc),
                "details": {
                    "supported_prefixes": ["AIza", "AQ"],
                },
            },
        )

    @app.exception_handler(AIUserKeyNetworkError)
    async def ai_user_key_network_error_handler(
        request: Request, exc: AIUserKeyNetworkError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=502,
            content={
                "success": False,
                "code": "AI_KEY_NETWORK_ERROR",
                "message": str(exc),
                "details": None,
            },
        )

    @app.exception_handler(AIUserKeyQuotaExceededError)
    async def ai_user_key_quota_error_handler(
        request: Request, exc: AIUserKeyQuotaExceededError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=429,
            content={
                "success": False,
                "code": "AI_KEY_QUOTA_EXCEEDED",
                "message": str(exc),
                "details": None,
            },
        )

    @app.exception_handler(AIUserKeyPermissionDeniedError)
    async def ai_user_key_permission_error_handler(
        request: Request, exc: AIUserKeyPermissionDeniedError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=403,
            content={
                "success": False,
                "code": "AI_KEY_PERMISSION_DENIED",
                "message": str(exc),
                "details": None,
            },
        )

    @app.exception_handler(AIUserKeyUnsupportedAuthKeyError)
    async def ai_user_key_unsupported_auth_key_handler(
        request: Request, exc: AIUserKeyUnsupportedAuthKeyError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "code": "AI_KEY_UNSUPPORTED_AUTH_KEY",
                "message": str(exc),
                "details": None,
            },
        )

    @app.exception_handler(AIUserKeySDKCompatibilityError)
    async def ai_user_key_sdk_compatibility_handler(
        request: Request, exc: AIUserKeySDKCompatibilityError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "code": "AI_KEY_SDK_INCOMPATIBLE",
                "message": str(exc),
                "details": None,
            },
        )

    @app.exception_handler(AIUserKeyUnknownError)
    async def ai_user_key_unknown_error_handler(
        request: Request, exc: AIUserKeyUnknownError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "code": "AI_KEY_UNKNOWN_ERROR",
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

    @app.exception_handler(AISessionExpiredError)
    async def ai_session_expired_handler(
        request: Request, exc: AISessionExpiredError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=401,
            content={
                "success": False,
                "code": "AI_SESSION_EXPIRED",
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

    @app.exception_handler(AssistantNoDataError)
    async def assistant_no_data_handler(
        request: Request, exc: AssistantNoDataError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "code": "ASSISTANT_NO_DATA",
                "message": str(exc),
                "details": None,
            },
        )

    @app.exception_handler(AssistantValidationError)
    async def assistant_validation_handler(
        request: Request, exc: AssistantValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=502,
            content={
                "success": False,
                "code": "ASSISTANT_VALIDATION_ERROR",
                "message": str(exc),
                "details": None,
            },
        )
