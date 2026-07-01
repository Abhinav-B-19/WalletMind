"""Domain-level exceptions for WalletMind services."""


class WalletMindError(Exception):
    """Base exception for WalletMind domain errors."""


class UserNotFoundError(WalletMindError):
    """Raised when a user does not exist in storage."""


class DuplicateUserError(WalletMindError):
    """Raised when creating/updating a duplicate user."""
