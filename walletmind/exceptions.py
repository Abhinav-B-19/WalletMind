"""Domain-level exceptions for WalletMind services."""


class WalletMindError(Exception):
    """Base exception for WalletMind domain errors."""


class UserNotFoundError(WalletMindError):
    """Raised when a user does not exist in storage."""


class DuplicateUserError(WalletMindError):
    """Raised when creating/updating a duplicate user."""


class StatementUploadError(WalletMindError):
    """Base exception for statement upload workflows."""


class StatementNotFoundError(StatementUploadError):
    """Raised when a statement does not exist in storage."""


class UnsupportedFileTypeError(StatementUploadError):
    """Raised when uploaded statement file extension is not supported."""


class EmptyFileError(StatementUploadError):
    """Raised when an uploaded file has no content."""


class FileTooLargeError(StatementUploadError):
    """Raised when an uploaded file exceeds configured max size."""


class StatementStorageError(StatementUploadError):
    """Raised when storage persistence operations fail."""


class NoTransactionsForStatementError(StatementUploadError):
    """Raised when a statement has no transactions for downstream analysis."""


class StatementInsightsError(WalletMindError):
    """Raised when AI insights generation fails."""
