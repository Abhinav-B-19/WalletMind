"""Centralized session-scoped Gemini API key resolution and storage."""

from __future__ import annotations

import logging
import secrets
import socket
import threading
from datetime import UTC, datetime, timedelta
from typing import Any, Literal, TypedDict

from backend.app.core.config import AppSettings, get_ai_settings
from backend.app.core.request_context import get_current_request
from backend.app.services.ai.exceptions import (
    AIConfigurationError,
    AISessionExpiredError,
    AIUserKeyInvalidError,
    AIUserKeyInvalidFormatError,
    AIUserKeyNetworkError,
    AIUserKeyPermissionDeniedError,
    AIUserKeyQuotaExceededError,
    AIUserKeySDKCompatibilityError,
    AIUserKeyUnsupportedAuthKeyError,
    AIUserKeyUnknownError,
)
from backend.app.services.ai.key_validation import get_default_key_validator_provider


class _SessionKeyEntry(TypedDict):
    api_key: str
    expires_at: datetime
    validated_at: datetime


KeySource = Literal["session", "developer", "none"]

_SESSION_ID_FIELD = "walletmind_session_id"
_CACHE_STATE_FIELD = "gemini_key_cache"
_CACHE_LOCK_FIELD = "gemini_key_cache_lock"
_SUPPORTED_KEY_PREFIXES = ("AIza", "AQ")
_MIN_REASONABLE_KEY_LENGTH = 8
_MAX_REASONABLE_KEY_LENGTH = 512

logger = logging.getLogger(__name__)


def _settings() -> AppSettings:
    return get_ai_settings()


def _get_bound_request() -> Any:
    request = get_current_request()
    if request is None:
        raise AIConfigurationError("Please configure your Gemini API key.")
    return request


def _cache_state(app: Any) -> tuple[dict[str, _SessionKeyEntry], threading.Lock]:
    cache = getattr(app.state, _CACHE_STATE_FIELD, None)
    if cache is None:
        cache = {}
        setattr(app.state, _CACHE_STATE_FIELD, cache)

    lock = getattr(app.state, _CACHE_LOCK_FIELD, None)
    if lock is None:
        lock = threading.Lock()
        setattr(app.state, _CACHE_LOCK_FIELD, lock)

    return cache, lock


def _now() -> datetime:
    return datetime.now(UTC)


def _session_max_age_seconds() -> int:
    return int(_settings().session_max_age_seconds)


def _ensure_session_id(*, request: Any) -> str:
    session = request.session
    session_id = session.get(_SESSION_ID_FIELD)
    if isinstance(session_id, str) and session_id.strip():
        return session_id

    session_id = secrets.token_urlsafe(32)
    session[_SESSION_ID_FIELD] = session_id
    return session_id


def _cleanup_expired(cache: dict[str, _SessionKeyEntry], *, now: datetime) -> None:
    expired = [
        session_id
        for session_id, entry in cache.items()
        if entry["expires_at"] <= now
    ]
    for session_id in expired:
        cache.pop(session_id, None)


def _to_utc_iso(value: datetime) -> str:
    return value.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _mask_key(api_key: str) -> str:
    """Mask key body while keeping short prefix/suffix for user recognition."""

    if not api_key:
        return ""

    if len(api_key) <= 8:
        return "*" * len(api_key)

    prefix_len = min(6, len(api_key) // 3)
    suffix_len = min(6, len(api_key) // 3)
    middle_len = max(len(api_key) - prefix_len - suffix_len, 4)

    return f"{api_key[:prefix_len]}{'*' * middle_len}{api_key[-suffix_len:]}"


def _mask_key_for_log(api_key: str) -> str:
    if not api_key:
        return ""
    if len(api_key) <= 4:
        return "*" * len(api_key)
    return f"{api_key[:4]}{'*' * max(len(api_key) - 4, 4)}"


def _resolve_session_entry() -> tuple[_SessionKeyEntry | None, str | None]:
    request = _get_bound_request()
    app = request.app
    session = request.session
    session_id = session.get(_SESSION_ID_FIELD)
    if not isinstance(session_id, str) or not session_id.strip():
        return None, None

    cache, lock = _cache_state(app)
    with lock:
        _cleanup_expired(cache, now=_now())
        entry = cache.get(session_id)

    if entry is None:
        request.session["walletmind_session_expired"] = True
    else:
        request.session.pop("walletmind_session_expired", None)

    return entry, session_id


def _validate_api_key_with_sdk(api_key: str) -> None:
    logger.info(
        "gemini_key_validation_requested",
        extra={"masked_api_key": _mask_key_for_log(api_key)},
    )

    _validate_api_key_sanity(api_key)
    logger.info("gemini_key_validation_sanity_accepted")

    validator = None
    request = get_current_request()
    if request is not None:
        validator = getattr(request.app.state, "gemini_api_key_validator", None)

    if callable(validator):
        logger.info("gemini_key_validation_custom_validator_used")
        if not bool(validator(api_key)):
            logger.warning("gemini_key_validation_custom_validator_rejected")
            raise AIUserKeyInvalidError("Unable to validate Gemini API key.")
        logger.info("gemini_key_validation_custom_validator_accepted")
        return

    try:
        provider = get_default_key_validator_provider()
        provider.validate(api_key)
        logger.info(
            "gemini_key_validation_google_response_received",
            extra={"provider": provider.provider_name},
        )
        logger.info("gemini_key_validation_succeeded")
    except Exception as exc:  # noqa: BLE001
        mapped_exc = _map_validation_exception(exc)
        sanitized_message = _sanitize_exception_message(exc=exc, api_key=api_key)
        logger.warning(
            "gemini_key_validation_failed",
            extra={
                "exception_class": type(exc).__name__,
                "exception_message": sanitized_message,
                "mapped_exception_class": type(mapped_exc).__name__,
            },
        )
        raise mapped_exc from exc


def _validate_api_key_sanity(api_key: str) -> None:
    """Perform minimal format-agnostic checks before SDK validation."""

    if not isinstance(api_key, str):
        logger.warning("gemini_key_validation_non_string_rejected")
        raise AIUserKeyInvalidFormatError(
            "This doesn't appear to be a supported Gemini credential."
        )

    length = len(api_key)
    if not any(api_key.startswith(prefix) for prefix in _SUPPORTED_KEY_PREFIXES):
        logger.warning("gemini_key_validation_prefix_rejected")
        raise AIUserKeyInvalidFormatError(
            "This doesn't appear to be a supported Gemini credential."
        )

    if length < _MIN_REASONABLE_KEY_LENGTH or length > _MAX_REASONABLE_KEY_LENGTH:
        logger.warning(
            "gemini_key_validation_length_rejected",
            extra={"key_length": length},
        )
        raise AIUserKeyInvalidFormatError(
            "This doesn't appear to be a supported Gemini credential."
        )


def _normalize_submitted_api_key(raw_value: str) -> str:
    """Normalize submitted API key by trimming whitespace and wrapper quotes."""

    normalized = raw_value.strip()
    if len(normalized) >= 2:
        if (
            (normalized.startswith("'") and normalized.endswith("'"))
            or (normalized.startswith('"') and normalized.endswith('"'))
        ):
            normalized = normalized[1:-1].strip()
    return normalized


def _sanitize_exception_message(*, exc: Exception, api_key: str) -> str:
    """Return exception message with potential key material redacted."""

    message = str(exc)
    if not message:
        return ""

    if api_key and api_key in message:
        return message.replace(api_key, "[REDACTED_KEY]")

    return message


def _friendly_validation_error_message(exc: Exception) -> str:
    """Map low-level validation failures to user-safe friendly messages."""

    message = str(exc).lower()

    if isinstance(exc, (TimeoutError, socket.timeout)):
        return "Gemini validation timed out. Please try again."

    if "quota" in message or "rate" in message:
        return "Gemini quota is currently exceeded. Please try again later."

    if "permission" in message or "forbidden" in message:
        return "Gemini API access was denied. Check API permissions and try again."

    if "invalid" in message and "api key" in message:
        return "Gemini API key appears invalid. Please verify and retry."

    if "unauth" in message or "401" in message:
        return "Gemini API key appears invalid. Please verify and retry."

    if "network" in message or "connection" in message or "dns" in message:
        return "Network issue while validating Gemini API key. Please retry."

    if "model" in message and ("not found" in message or "unavailable" in message):
        return "Gemini models are currently unavailable. Please try again later."

    if "import" in message or "module" in message:
        return "Gemini SDK initialization failed. Contact support."

    return "Unable to validate Gemini API key."


def _map_validation_exception(exc: Exception) -> Exception:
    """Map low-level SDK exceptions to API-safe key validation exceptions."""

    message = str(exc).lower()

    if isinstance(exc, AIUserKeyInvalidFormatError):
        return exc

    if isinstance(exc, (TimeoutError, socket.timeout)):
        return AIUserKeyNetworkError("Network issue while validating Gemini API key.")

    if "quota" in message or "rate" in message:
        return AIUserKeyQuotaExceededError(
            "Gemini quota is currently exceeded. Please try again later."
        )

    if "permission" in message or "forbidden" in message:
        return AIUserKeyPermissionDeniedError(
            "Gemini API access was denied. Check API permissions and try again."
        )

    if "unsupported" in message and ("auth" in message or "authorization" in message):
        return AIUserKeyUnsupportedAuthKeyError(
            "Submitted Gemini auth key type is unsupported by current validation flow."
        )

    if "sdk" in message and ("incompat" in message or "unsupported" in message):
        return AIUserKeySDKCompatibilityError(
            "Installed Gemini SDK appears incompatible with this auth key validation flow."
        )

    if (
        ("invalid" in message and "api key" in message)
        or "unauth" in message
        or "401" in message
    ):
        return AIUserKeyInvalidError(
            "Gemini API key appears invalid. Please verify and retry."
        )

    if "network" in message or "connection" in message or "dns" in message:
        return AIUserKeyNetworkError("Network issue while validating Gemini API key.")

    return AIUserKeyUnknownError("Unable to validate Gemini API key.")


def store_session_gemini_key(*, api_key: str) -> None:
    """Validate and store a user-provided Gemini API key for this session."""

    normalized = _normalize_submitted_api_key(api_key)
    if not normalized:
        logger.warning("gemini_key_validation_empty_input")
        raise AIUserKeyInvalidFormatError(
            "This doesn't appear to be a supported Gemini credential."
        )

    _validate_api_key_with_sdk(normalized)

    request = _get_bound_request()
    session_id = _ensure_session_id(request=request)
    app = request.app
    cache, lock = _cache_state(app)

    expires_at = _now() + timedelta(seconds=_session_max_age_seconds())
    with lock:
        _cleanup_expired(cache, now=_now())
        validated_at = _now()
        cache[session_id] = {
            "api_key": normalized,
            "expires_at": expires_at,
            "validated_at": validated_at,
        }

    logger.info("gemini_key_session_storage_succeeded")


def delete_session_gemini_key() -> bool:
    """Delete currently configured Gemini API key for this request session."""

    request = _get_bound_request()
    session_id = request.session.get(_SESSION_ID_FIELD)
    if not isinstance(session_id, str) or not session_id.strip():
        return False

    cache, lock = _cache_state(request.app)
    with lock:
        removed = cache.pop(session_id, None)

    return removed is not None


def clear_request_session() -> None:
    """Clear session-scoped Gemini key and reset signed session cookie state."""

    request = _get_bound_request()
    delete_session_gemini_key()
    request.session.clear()


def _resolve_developer_fallback_key() -> str | None:
    settings = _settings()
    if not settings.developer_mode:
        return None

    fallback = settings.gemini_api_key.strip()
    if not fallback:
        return None

    return fallback


def get_active_gemini_key() -> str:
    """Return active Gemini key resolved from session first, then developer fallback."""

    entry, _session_id = _resolve_session_entry()
    if entry is not None:
        return entry["api_key"]

    request = get_current_request()
    if request is not None and request.session.get("walletmind_session_expired"):
        raise AISessionExpiredError("Your AI session has expired.")

    fallback = _resolve_developer_fallback_key()
    if fallback is not None:
        return fallback

    raise AIConfigurationError("Please configure your Gemini API key.")


def get_gemini_key_status() -> dict[str, Any]:
    """Return non-sensitive key configuration status for the current request."""

    source: KeySource = "none"
    configured = False
    masked_key: str | None = None
    last_validated: str | None = None
    model = _settings().gemini_model

    entry, _session_id = _resolve_session_entry()
    if entry is not None:
        configured = True
        source = "session"
        masked_key = _mask_key(entry["api_key"])
        last_validated = _to_utc_iso(entry["validated_at"])
    else:
        fallback = _resolve_developer_fallback_key()
        if fallback is not None:
            configured = True
            source = "developer"

    return {
        "configured": configured,
        "masked_key": masked_key,
        "source": source,
        "model": model,
        "last_validated": last_validated,
    }


def get_session_gemini_key_for_owner() -> str | None:
    """Return full session key for explicit owner reveal flows only."""

    entry, _session_id = _resolve_session_entry()
    if entry is None:
        return None
    return entry["api_key"]
