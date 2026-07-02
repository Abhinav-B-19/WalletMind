"""Reusable statement upload business logic independent of FastAPI."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from backend.app.models.statement import Statement, StatementStatus
from backend.app.models.user import User
from walletmind.exceptions import (
    EmptyFileError,
    FileTooLargeError,
    StatementNotFoundError,
    StatementStorageError,
    UnsupportedFileTypeError,
    UserNotFoundError,
)
from walletmind.schemas.statement import UploadResponseDTO
from walletmind.utils.file_uploads import (
    EXTENSION_TO_PARSER_TYPE,
    generate_stored_filename,
    normalized_extension,
    parser_type_for_extension,
    sanitize_filename,
)


class StatementUploadService:
    """Handles statement file validation, storage, and metadata persistence."""

    def __init__(
        self,
        *,
        session_factory: sessionmaker[Session],
        upload_dir: Path,
        max_file_size_bytes: int = 10 * 1024 * 1024,
        allowed_extensions: set[str] | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._upload_dir = Path(upload_dir)
        self._max_file_size_bytes = max_file_size_bytes
        self._allowed_extensions = allowed_extensions or set(EXTENSION_TO_PARSER_TYPE)

    def upload_statement(
        self,
        *,
        user_uuid: UUID | str,
        original_filename: str,
        file_bytes: bytes,
    ) -> UploadResponseDTO:
        """Validate, persist, and return metadata for an uploaded statement."""

        parsed_user_uuid = self._coerce_uuid(user_uuid)
        clean_filename = sanitize_filename(original_filename)
        extension = normalized_extension(clean_filename)
        if extension not in self._allowed_extensions:
            raise UnsupportedFileTypeError(
                "Unsupported file type. Allowed formats are .csv, .xls, .xlsx, .pdf"
            )
        parser_type = parser_type_for_extension(extension)
        if parser_type is None:
            raise UnsupportedFileTypeError(
                "Unsupported file type. Allowed formats are .csv, .xls, .xlsx, .pdf"
            )

        file_size = len(file_bytes)
        if file_size == 0:
            raise EmptyFileError("Uploaded file is empty")
        if file_size > self._max_file_size_bytes:
            raise FileTooLargeError("Uploaded file exceeds maximum allowed size")

        self._upload_dir.mkdir(parents=True, exist_ok=True)
        stored_filename = generate_stored_filename(extension)
        file_path = self._upload_dir / stored_filename

        try:
            file_path.write_bytes(file_bytes)
        except OSError as exc:
            raise StatementStorageError("Failed to store uploaded statement file") from exc

        try:
            with self._session_factory() as session:
                user = session.scalar(select(User).where(User.uuid == str(parsed_user_uuid)))
                if user is None:
                    self._safe_delete_file(file_path)
                    raise UserNotFoundError(f"User '{parsed_user_uuid}' was not found")

                statement = Statement(
                    user_id=user.id,
                    original_filename=clean_filename,
                    stored_filename=stored_filename,
                    file_type=extension.lstrip("."),
                    file_size=file_size,
                    status=StatementStatus.UPLOADED,
                    bank_name=None,
                )
                session.add(statement)
                session.commit()
                session.refresh(statement)
                return self._to_upload_response(statement, parser_type=parser_type)
        except (UserNotFoundError, UnsupportedFileTypeError, EmptyFileError, FileTooLargeError):
            raise
        except SQLAlchemyError as exc:
            self._safe_delete_file(file_path)
            raise StatementStorageError("Failed to persist statement metadata") from exc

    def list_statements(self, user_uuid: UUID | str | None = None) -> list[UploadResponseDTO]:
        """Return all uploaded statement metadata records."""

        parsed_user_uuid: UUID | None = None
        if user_uuid is not None:
            parsed_user_uuid = self._coerce_uuid(user_uuid)

        with self._session_factory() as session:
            query = select(Statement).order_by(Statement.uploaded_at.desc(), Statement.id.desc())
            if parsed_user_uuid is not None:
                query = query.join(User).where(User.uuid == str(parsed_user_uuid))

            statements = session.scalars(query).all()
            return [
                self._to_upload_response(
                    statement,
                    parser_type=parser_type_for_extension(f".{statement.file_type}")
                    or "unknown",
                )
                for statement in statements
            ]

    def get_statement(self, statement_uuid: UUID | str) -> UploadResponseDTO:
        """Return metadata for a single statement."""

        parsed_statement_uuid = self._coerce_uuid(statement_uuid)
        with self._session_factory() as session:
            statement = session.scalar(
                select(Statement).where(Statement.uuid == str(parsed_statement_uuid))
            )
            if statement is None:
                raise StatementNotFoundError(
                    f"Statement '{parsed_statement_uuid}' was not found"
                )
            return self._to_upload_response(
                statement,
                parser_type=parser_type_for_extension(f".{statement.file_type}")
                or "unknown",
            )

    def delete_statement(self, statement_uuid: UUID | str) -> None:
        """Delete statement metadata and the uploaded file."""

        parsed_statement_uuid = self._coerce_uuid(statement_uuid)
        with self._session_factory() as session:
            statement = session.scalar(
                select(Statement).where(Statement.uuid == str(parsed_statement_uuid))
            )
            if statement is None:
                raise StatementNotFoundError(
                    f"Statement '{parsed_statement_uuid}' was not found"
                )

            file_path = self._upload_dir / statement.stored_filename
            try:
                file_path.unlink(missing_ok=True)
            except OSError as exc:
                raise StatementStorageError("Failed to delete uploaded statement file") from exc

            try:
                session.delete(statement)
                session.commit()
            except SQLAlchemyError as exc:
                raise StatementStorageError("Failed to delete statement metadata") from exc

    @staticmethod
    def _coerce_uuid(value: UUID | str) -> UUID:
        if isinstance(value, UUID):
            return value
        return UUID(str(value))

    @staticmethod
    def _to_upload_response(statement: Statement, *, parser_type: str) -> UploadResponseDTO:
        return UploadResponseDTO(
            statement_uuid=UUID(statement.uuid),
            original_filename=statement.original_filename,
            stored_filename=statement.stored_filename,
            file_size=statement.file_size,
            file_type=statement.file_type,
            parser_type=parser_type,
            bank_name=statement.bank_name,
            analysis_status=StatementStatus.UPLOADED,
            status=StatementStatus.UPLOADED,
            uploaded_at=statement.uploaded_at,
        )

    @staticmethod
    def _safe_delete_file(path: Path) -> None:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass
