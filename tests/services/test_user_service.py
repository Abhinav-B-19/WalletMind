from __future__ import annotations

from uuid import uuid4

import pytest
from pydantic import ValidationError

from walletmind.exceptions import DuplicateUserError, UserNotFoundError
from walletmind.services.user_service import UserService


def test_create_and_get_user() -> None:
    service = UserService()

    created = service.create_user(
        {
            "name": "Alex",
            "occupation": "Engineer",
            "monthly_income": 6000,
        }
    )

    fetched = service.get_user_by_uuid(created.id)

    assert fetched == created


def test_list_users_returns_all_created_users() -> None:
    service = UserService()

    first = service.create_user(
        {
            "name": "Alex",
            "occupation": "Engineer",
            "monthly_income": 6000,
        }
    )
    second = service.create_user(
        {
            "name": "Mina",
            "occupation": "Designer",
            "monthly_income": 5400,
        }
    )

    users = service.list_users()

    assert len(users) == 2
    assert {first.id, second.id} == {user.id for user in users}


def test_update_user_updates_selected_fields() -> None:
    service = UserService()
    created = service.create_user(
        {
            "name": "Alex",
            "occupation": "Engineer",
            "monthly_income": 6000,
        }
    )

    updated = service.update_user(
        created.id,
        {
            "occupation": "Senior Engineer",
            "monthly_income": 7200,
        },
    )

    assert updated.id == created.id
    assert updated.name == "Alex"
    assert updated.occupation == "Senior Engineer"
    assert updated.monthly_income == 7200


def test_delete_user_removes_user() -> None:
    service = UserService()
    created = service.create_user(
        {
            "name": "Alex",
            "occupation": "Engineer",
            "monthly_income": 6000,
        }
    )

    service.delete_user(created.id)

    with pytest.raises(UserNotFoundError):
        service.get_user_by_uuid(created.id)


def test_create_user_rejects_duplicate_name_and_occupation() -> None:
    service = UserService()
    service.create_user(
        {
            "name": "Alex",
            "occupation": "Engineer",
            "monthly_income": 6000,
        }
    )

    with pytest.raises(DuplicateUserError):
        service.create_user(
            {
                "name": "  alex  ",
                "occupation": " engineer ",
                "monthly_income": 7000,
            }
        )


def test_update_user_rejects_duplicate_name_and_occupation() -> None:
    service = UserService()
    service.create_user(
        {
            "name": "Alex",
            "occupation": "Engineer",
            "monthly_income": 6000,
        }
    )
    other = service.create_user(
        {
            "name": "Mina",
            "occupation": "Designer",
            "monthly_income": 5400,
        }
    )

    with pytest.raises(DuplicateUserError):
        service.update_user(other.id, {"name": "Alex", "occupation": "Engineer"})


def test_create_user_validates_required_fields() -> None:
    service = UserService()

    with pytest.raises(ValidationError):
        service.create_user(
            {
                "name": "",
                "occupation": "Engineer",
                "monthly_income": 6000,
            }
        )


def test_create_user_validates_monthly_income() -> None:
    service = UserService()

    with pytest.raises(ValidationError):
        service.create_user(
            {
                "name": "Alex",
                "occupation": "Engineer",
                "monthly_income": 0,
            }
        )


def test_update_user_validates_monthly_income() -> None:
    service = UserService()
    created = service.create_user(
        {
            "name": "Alex",
            "occupation": "Engineer",
            "monthly_income": 6000,
        }
    )

    with pytest.raises(ValidationError):
        service.update_user(created.id, {"monthly_income": -100})


def test_non_existent_user_operations_raise_not_found() -> None:
    service = UserService()
    missing_user_id = uuid4()

    with pytest.raises(UserNotFoundError):
        service.get_user_by_uuid(missing_user_id)

    with pytest.raises(UserNotFoundError):
        service.update_user(missing_user_id, {"name": "New Name"})

    with pytest.raises(UserNotFoundError):
        service.delete_user(missing_user_id)
