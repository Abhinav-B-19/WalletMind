"""Reusable user business logic independent from web frameworks."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Mapping
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from backend.app.models.user import User as UserModel
from walletmind.exceptions import DuplicateUserError, UserNotFoundError
from walletmind.schemas.user import UserCreateDTO, UserDTO, UserUpdateDTO


@dataclass
class _UserRecord:
    """Internal storage model used by the service."""

    id: UUID
    name: str
    occupation: str
    monthly_income: float
    currency: str
    primary_financial_goal: str


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

    def __init__(
        self,
        store: InMemoryUserStore | None = None,
        session_factory: sessionmaker[Session] | None = None,
    ) -> None:
        self._store = store or InMemoryUserStore()
        self._session_factory = session_factory

    def create_user(self, payload: UserCreateDTO | Mapping[str, Any]) -> UserDTO:
        create_dto = self._validate_create(payload)
        if self._session_factory is not None:
            return self._create_user_db(create_dto)

        self._ensure_unique(
            name=create_dto.name,
            occupation=create_dto.occupation,
        )
        record = _UserRecord(
            id=uuid4(),
            name=create_dto.name,
            occupation=create_dto.occupation,
            monthly_income=create_dto.monthly_income,
            currency=create_dto.currency,
            primary_financial_goal=create_dto.primary_financial_goal,
        )
        self._store.add(record)
        return self._to_dto(record)

    def get_user_by_uuid(self, user_id: UUID) -> UserDTO:
        if self._session_factory is not None:
            return self._get_user_db(user_id)

        record = self._store.get(user_id)
        if record is None:
            raise UserNotFoundError(f"User '{user_id}' was not found")
        return self._to_dto(record)

    def update_user(
        self, user_id: UUID, payload: UserUpdateDTO | Mapping[str, Any]
    ) -> UserDTO:
        update_dto = self._validate_update(payload)
        if self._session_factory is not None:
            return self._update_user_db(user_id, update_dto)

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
        if "currency" in updates:
            record.currency = updates["currency"]
        if "primary_financial_goal" in updates:
            record.primary_financial_goal = updates["primary_financial_goal"]
        return self._to_dto(record)

    def delete_user(self, user_id: UUID) -> None:
        if self._session_factory is not None:
            self._delete_user_db(user_id)
            return

        deleted = self._store.remove(user_id)
        if not deleted:
            raise UserNotFoundError(f"User '{user_id}' was not found")

    def list_users(self) -> list[UserDTO]:
        if self._session_factory is not None:
            return self._list_users_db()

        return [self._to_dto(record) for record in self._store.list()]

    def _create_user_db(self, create_dto: UserCreateDTO) -> UserDTO:
        with self._session_factory() as session:
            self._ensure_unique_db(
                session,
                name=create_dto.name,
                occupation=create_dto.occupation,
            )
            user = UserModel(
                full_name=create_dto.name,
                occupation=create_dto.occupation,
                monthly_income=Decimal(str(create_dto.monthly_income)),
                currency=create_dto.currency,
                financial_goal=create_dto.primary_financial_goal,
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            return self._to_dto_db(user)

    def _get_user_db(self, user_id: UUID) -> UserDTO:
        with self._session_factory() as session:
            user = session.scalar(select(UserModel).where(UserModel.uuid == str(user_id)))
            if user is None:
                raise UserNotFoundError(f"User '{user_id}' was not found")
            return self._to_dto_db(user)

    def _update_user_db(self, user_id: UUID, update_dto: UserUpdateDTO) -> UserDTO:
        with self._session_factory() as session:
            user = session.scalar(select(UserModel).where(UserModel.uuid == str(user_id)))
            if user is None:
                raise UserNotFoundError(f"User '{user_id}' was not found")

            updates = update_dto.model_dump(exclude_unset=True)
            next_name = updates.get("name", user.full_name)
            next_occupation = updates.get("occupation", user.occupation)
            self._ensure_unique_db(
                session,
                name=next_name,
                occupation=next_occupation,
                excluding_user_uuid=user.uuid,
            )

            user.full_name = next_name
            user.occupation = next_occupation
            if "monthly_income" in updates:
                user.monthly_income = Decimal(str(updates["monthly_income"]))
            if "currency" in updates:
                user.currency = updates["currency"]
            if "primary_financial_goal" in updates:
                user.financial_goal = updates["primary_financial_goal"]
            session.commit()
            session.refresh(user)
            return self._to_dto_db(user)

    def _delete_user_db(self, user_id: UUID) -> None:
        with self._session_factory() as session:
            user = session.scalar(select(UserModel).where(UserModel.uuid == str(user_id)))
            if user is None:
                raise UserNotFoundError(f"User '{user_id}' was not found")
            session.delete(user)
            session.commit()

    def _list_users_db(self) -> list[UserDTO]:
        with self._session_factory() as session:
            users = session.scalars(select(UserModel).order_by(UserModel.id.asc())).all()
            return [self._to_dto_db(user) for user in users]

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

    def _ensure_unique_db(
        self,
        session: Session,
        *,
        name: str,
        occupation: str,
        excluding_user_uuid: str | None = None,
    ) -> None:
        name_key = self._normalize_identity_value(name)
        occupation_key = self._normalize_identity_value(occupation)
        users = session.scalars(select(UserModel)).all()
        for existing in users:
            if excluding_user_uuid is not None and existing.uuid == excluding_user_uuid:
                continue
            if (
                self._normalize_identity_value(existing.full_name) == name_key
                and self._normalize_identity_value(existing.occupation or "")
                == occupation_key
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
            currency=record.currency,
            primary_financial_goal=record.primary_financial_goal,
        )

    @staticmethod
    def _to_dto_db(record: UserModel) -> UserDTO:
        return UserDTO(
            id=UUID(record.uuid),
            name=record.full_name,
            occupation=record.occupation or "",
            monthly_income=float(record.monthly_income),
            currency=record.currency,
            primary_financial_goal=record.financial_goal,
        )
