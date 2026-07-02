from __future__ import annotations

import pytest
from sqlalchemy import delete

from backend.app.database.session import SessionLocal
from backend.app.models.statement import Statement
from backend.app.models.user import User
from fastapi.testclient import TestClient

from backend.app.main import create_app


@pytest.fixture(autouse=True)
def _reset_database() -> None:
    with SessionLocal() as session:
        session.execute(delete(Statement))
        session.execute(delete(User))
        session.commit()


def _create_user_payload(
    name: str = "Alex",
    occupation: str = "Engineer",
    monthly_income: float = 6000,
) -> dict[str, str | float]:
    return {
        "name": name,
        "occupation": occupation,
        "monthly_income": monthly_income,
    }


def test_create_user_success() -> None:
    app = create_app()
    client = TestClient(app)

    response = client.post("/api/v1/users", json=_create_user_payload())

    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "User created successfully."
    assert body["data"]["name"] == "Alex"
    assert body["data"]["occupation"] == "Engineer"
    assert body["data"]["monthly_income"] == 6000
    assert "id" in body["data"]


def test_create_user_validation_failure() -> None:
    app = create_app()
    client = TestClient(app)

    response = client.post(
        "/api/v1/users",
        json=_create_user_payload(monthly_income=0),
    )

    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert body["code"] == "VALIDATION_ERROR"
    assert body["message"] == "Request validation failed"
    assert isinstance(body["details"], list)


def test_get_user_success() -> None:
    app = create_app()
    client = TestClient(app)

    create_response = client.post("/api/v1/users", json=_create_user_payload())
    user_id = create_response.json()["data"]["id"]

    response = client.get(f"/api/v1/users/{user_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "User retrieved successfully."
    assert body["data"]["id"] == user_id


def test_get_user_validation_failure_for_invalid_uuid() -> None:
    app = create_app()
    client = TestClient(app)

    response = client.get("/api/v1/users/not-a-uuid")

    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert body["code"] == "VALIDATION_ERROR"


def test_update_user_success() -> None:
    app = create_app()
    client = TestClient(app)

    create_response = client.post("/api/v1/users", json=_create_user_payload())
    user_id = create_response.json()["data"]["id"]

    response = client.put(
        f"/api/v1/users/{user_id}",
        json={"occupation": "Senior Engineer", "monthly_income": 7500},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "User updated successfully."
    assert body["data"]["occupation"] == "Senior Engineer"
    assert body["data"]["monthly_income"] == 7500


def test_update_user_validation_failure() -> None:
    app = create_app()
    client = TestClient(app)

    create_response = client.post("/api/v1/users", json=_create_user_payload())
    user_id = create_response.json()["data"]["id"]

    response = client.put(
        f"/api/v1/users/{user_id}",
        json={"monthly_income": -10},
    )

    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert body["code"] == "VALIDATION_ERROR"


def test_delete_user_success() -> None:
    app = create_app()
    client = TestClient(app)

    create_response = client.post("/api/v1/users", json=_create_user_payload())
    user_id = create_response.json()["data"]["id"]

    delete_response = client.delete(f"/api/v1/users/{user_id}")

    assert delete_response.status_code == 200
    delete_body = delete_response.json()
    assert delete_body["success"] is True
    assert delete_body["message"] == "User deleted successfully."
    assert delete_body["data"]["user_uuid"] == user_id
    assert delete_body["data"]["status"] == "deleted"

    get_response = client.get(f"/api/v1/users/{user_id}")
    assert get_response.status_code == 404


def test_delete_user_validation_failure_for_invalid_uuid() -> None:
    app = create_app()
    client = TestClient(app)

    response = client.delete("/api/v1/users/not-a-uuid")

    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert body["code"] == "VALIDATION_ERROR"


def test_list_users_success() -> None:
    app = create_app()
    client = TestClient(app)

    client.post("/api/v1/users", json=_create_user_payload(name="Alex"))
    client.post(
        "/api/v1/users",
        json=_create_user_payload(name="Mina", occupation="Designer"),
    )

    response = client.get("/api/v1/users")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "Users retrieved successfully."
    assert isinstance(body["data"], list)
    assert len(body["data"]) == 2


def test_duplicate_user_returns_standardized_error() -> None:
    app = create_app()
    client = TestClient(app)

    client.post("/api/v1/users", json=_create_user_payload())
    response = client.post(
        "/api/v1/users",
        json=_create_user_payload(name=" alex ", occupation=" engineer "),
    )

    assert response.status_code == 409
    body = response.json()
    assert body["success"] is False
    assert body["code"] == "DUPLICATE_USER"
    assert "already exists" in body["message"]
