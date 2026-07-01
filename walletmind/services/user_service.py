"""Reusable user business logic independent from web frameworks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping
from uuid import UUID, uuid4

from walletmind.exceptions import DuplicateUserError, UserNotFoundError
from walletmind.schemas.user import UserCreateDTO, UserDTO, UserUpdateDTO


@dataclass
class _UserRecord:
    """Internal storage model used by the service."""

    id: UUID
    name: str
    occupation: str
    monthly_income: float


class InMemoryUserStore:
    """In-memory storage implementation useful for unit tests and notebooks."""

    def __init__(self) -> None:
        self._records: dict[UUID, _UserRecord] = {}

    def add(self, record: _UserRecord) -> _UserRecord:
        self._records[record.id] = record
        return record

    def get(self, user_id: UUID) -> _UserRecord | None:
        return self._records.get(user_id)

    def remove(self, user_id: UUID) -> bool:
        return self._records.pop(user_id, None) is not None

    def list(self) -> list[_UserRecord]:
        return list(self._records.values())


class UserService:
    """Provides CRUD business logic for users."""

    def __init__(self, store: InMemoryUserStore | None = None) -> None:
        self._store = store or InMemoryUserStore()

    def create_user(self, payload: UserCreateDTO | Mapping[str, Any]) -> UserDTO:
        create_dto = self._validate_create(payload)
        self._ensure_unique(
            name=create_dto.name,
            occupation=create_dto.occupation,
        )
        record = _UserRecord(
            id=uuid4(),
            name=create_dto.name,
            occupation=create_dto.occupation,
            monthly_income=create_dto.monthly_income,
        )
        self._store.add(record)
        return self._to_dto(record)

    def get_user_by_uuid(self, user_id: UUID) -> UserDTO:
        record = self._store.get(user_id)
        if record is None:
            raise UserNotFoundError(f"User '{user_id}' was not found")
        return self._to_dto(record)

    def update_user(
        self, user_id: UUID, payload: UserUpdateDTO | Mapping[str, Any]
    ) -> UserDTO:
        update_dto = self._validate_update(payload)
        record = self._store.get(user_id)
        if record is None:
            raise UserNotFoundError(f"User '{user_id}' was not found")

        updates = update_dto.model_dump(exclude_unset=True)
        next_name = updates.get("name", record.name)
        next_occupation = updates.get("occupation", record.occupation)

        self._ensure_unique(
            name=next_name,
            occupation=next_occupation,
            excluding_user_id=user_id,
        )

        record.name = next_name
        record.occupation = next_occupation
        if "monthly_income" in updates:
            record.monthly_income = updates["monthly_income"]
        return self._to_dto(record)

    def delete_user(self, user_id: UUID) -> None:
        deleted = self._store.remove(user_id)
        if not deleted:
            raise UserNotFoundError(f"User '{user_id}' was not found")

    def list_users(self) -> list[UserDTO]:
        return [self._to_dto(record) for record in self._store.list()]

    def _validate_create(self, payload: UserCreateDTO | Mapping[str, Any]) -> UserCreateDTO:
        if isinstance(payload, UserCreateDTO):
            return payload
        return UserCreateDTO.model_validate(payload)

    def _validate_update(self, payload: UserUpdateDTO | Mapping[str, Any]) -> UserUpdateDTO:
        if isinstance(payload, UserUpdateDTO):
            return payload
        return UserUpdateDTO.model_validate(payload)

    def _ensure_unique(
        self,
        *,
        name: str,
        occupation: str,
        excluding_user_id: UUID | None = None,
    ) -> None:
        name_key = self._normalize_identity_value(name)
        occupation_key = self._normalize_identity_value(occupation)
        for existing in self._store.list():
            if excluding_user_id is not None and existing.id == excluding_user_id:
                continue
            if (
                self._normalize_identity_value(existing.name) == name_key
                and self._normalize_identity_value(existing.occupation) == occupation_key
            ):
                raise DuplicateUserError(
                    "User with the same name and occupation already exists"
                )

    @staticmethod
    def _normalize_identity_value(value: str) -> str:
        return value.strip().casefold()

    @staticmethod
    def _to_dto(record: _UserRecord) -> UserDTO:
        return UserDTO(
            id=record.id,
            name=record.name,
            occupation=record.occupation,
            monthly_income=record.monthly_income,
        )
