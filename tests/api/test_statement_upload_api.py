from __future__ import annotations

from decimal import Decimal

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import select
from sqlalchemy import delete

from backend.app.database.init_db import init_database
from backend.app.database.session import SessionLocal, create_database_engine, create_session_factory
from backend.app.main import create_app
from backend.app.models.statement import Statement
from backend.app.models.user import User
from walletmind.services.statement_upload_service import StatementUploadService


@pytest.fixture(autouse=True)
def _reset_database() -> None:
    with SessionLocal() as session:
        session.execute(delete(Statement))
        session.execute(delete(User))
        session.commit()


def _setup_client_with_statement_service(tmp_path):
    database_url = f"sqlite+pysqlite:///{(tmp_path / 'api-test.db').as_posix()}"
    database_engine = create_database_engine(database_url)
    session_factory = create_session_factory(database_engine)
    init_database(database_engine)

    app = create_app()
    app.state.statement_upload_service = StatementUploadService(
        session_factory=session_factory,
        upload_dir=tmp_path / "uploads",
    )

    client = TestClient(app)
    return client, session_factory


def _create_persisted_user(session_factory) -> User:
    with session_factory() as session:
        user = User(
            full_name="Avery Quinn",
            occupation="Engineer",
            monthly_income=Decimal("6400.00"),
            currency="USD",
            financial_goal="Budget optimization.",
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


def test_statement_upload_endpoint(tmp_path) -> None:
    client, session_factory = _setup_client_with_statement_service(tmp_path)
    user = _create_persisted_user(session_factory)

    response = client.post(
        "/api/v1/statements/upload",
        data={"user_uuid": user.uuid},
        files={"file": ("june.csv", b"date,amount\n2026-06-01,120\n", "text/csv")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "Statement uploaded successfully."
    assert body["data"]["statement_uuid"]
    assert body["data"]["original_filename"] == "june.csv"
    assert body["data"]["file_type"] == "csv"
    assert body["data"]["analysis_status"] == "uploaded"
    assert body["data"]["status"] == "uploaded"


def test_statement_list_endpoint(tmp_path) -> None:
    client, session_factory = _setup_client_with_statement_service(tmp_path)
    user = _create_persisted_user(session_factory)

    client.post(
        "/api/v1/statements/upload",
        data={"user_uuid": user.uuid},
        files={"file": ("june.csv", b"date,amount\n2026-06-01,120\n", "text/csv")},
    )

    response = client.get("/api/v1/statements")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "Statements retrieved successfully."
    assert isinstance(body["data"], list)
    assert len(body["data"]) == 1
    assert body["data"][0]["original_filename"] == "june.csv"


def test_statement_list_endpoint_filters_by_user_uuid(tmp_path) -> None:
    client, session_factory = _setup_client_with_statement_service(tmp_path)
    user_one = _create_persisted_user(session_factory)
    with session_factory() as session:
        user_two = User(
            full_name="Mila Roe",
            occupation="Designer",
            monthly_income=Decimal("5100.00"),
            currency="USD",
            financial_goal="Reduce discretionary spending.",
        )
        session.add(user_two)
        session.commit()
        session.refresh(user_two)

    client.post(
        "/api/v1/statements/upload",
        data={"user_uuid": user_one.uuid},
        files={"file": ("u1.csv", b"date,amount\n2026-06-01,120\n", "text/csv")},
    )
    client.post(
        "/api/v1/statements/upload",
        data={"user_uuid": user_two.uuid},
        files={"file": ("u2.csv", b"date,amount\n2026-06-01,220\n", "text/csv")},
    )

    response = client.get(f"/api/v1/statements?user_uuid={user_one.uuid}")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "Statements retrieved successfully."
    assert len(body["data"]) == 1
    assert body["data"][0]["original_filename"] == "u1.csv"


def test_statement_upload_list_delete_workflow(tmp_path) -> None:
    client, session_factory = _setup_client_with_statement_service(tmp_path)
    user = _create_persisted_user(session_factory)

    upload_response = client.post(
        "/api/v1/statements/upload",
        data={"user_uuid": user.uuid},
        files={"file": ("workflow.csv", b"date,amount\n2026-08-01,500\n", "text/csv")},
    )
    assert upload_response.status_code == 201
    statement_uuid = upload_response.json()["data"]["statement_uuid"]

    list_response = client.get("/api/v1/statements")
    assert list_response.status_code == 200
    listed = list_response.json()
    assert listed["success"] is True
    assert listed["message"] == "Statements retrieved successfully."
    assert len(listed["data"]) == 1
    assert listed["data"][0]["statement_uuid"] == statement_uuid

    delete_response = client.delete(f"/api/v1/statements/{statement_uuid}")
    assert delete_response.status_code == 200
    delete_body = delete_response.json()
    assert delete_body["success"] is True
    assert delete_body["message"] == "Statement deleted successfully."
    assert delete_body["data"]["statement_uuid"] == statement_uuid
    assert delete_body["data"]["status"] == "deleted"

    list_after_delete_response = client.get("/api/v1/statements")
    assert list_after_delete_response.status_code == 200
    list_after_delete_body = list_after_delete_response.json()
    assert list_after_delete_body["success"] is True
    assert list_after_delete_body["message"] == "Statements retrieved successfully."
    assert list_after_delete_body["data"] == []


def test_statement_get_endpoint(tmp_path) -> None:
    client, session_factory = _setup_client_with_statement_service(tmp_path)
    user = _create_persisted_user(session_factory)

    upload_response = client.post(
        "/api/v1/statements/upload",
        data={"user_uuid": user.uuid},
        files={"file": ("july.xlsx", b"PK\x03\x04xlsx-content", "application/vnd.ms-excel")},
    )
    statement_uuid = upload_response.json()["data"]["statement_uuid"]

    response = client.get(f"/api/v1/statements/{statement_uuid}")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "Statement retrieved successfully."
    assert body["data"]["statement_uuid"] == statement_uuid
    assert body["data"]["original_filename"] == "july.xlsx"


def test_statement_delete_endpoint(tmp_path) -> None:
    client, session_factory = _setup_client_with_statement_service(tmp_path)
    user = _create_persisted_user(session_factory)

    upload_response = client.post(
        "/api/v1/statements/upload",
        data={"user_uuid": user.uuid},
        files={"file": ("aug.csv", b"date,amount\n2026-08-01,200\n", "text/csv")},
    )
    body = upload_response.json()["data"]
    statement_uuid = body["statement_uuid"]
    stored_filename = body["stored_filename"]

    delete_response = client.delete(f"/api/v1/statements/{statement_uuid}")

    assert delete_response.status_code == 200
    delete_body = delete_response.json()
    assert delete_body["success"] is True
    assert delete_body["message"] == "Statement deleted successfully."
    assert delete_body["data"]["statement_uuid"] == statement_uuid
    assert delete_body["data"]["status"] == "deleted"
    assert not (tmp_path / "uploads" / stored_filename).exists()

    get_response = client.get(f"/api/v1/statements/{statement_uuid}")
    assert get_response.status_code == 404
    get_error = get_response.json()
    assert get_error["success"] is False
    assert get_error["code"] == "STATEMENT_NOT_FOUND"


def test_create_user_then_upload_statement_uses_same_database() -> None:
    app = create_app()
    client = TestClient(app)

    create_user_response = client.post(
        "/api/v1/users",
        json={
            "name": "Jordan Blake",
            "occupation": "Analyst",
            "monthly_income": 6100,
        },
    )
    assert create_user_response.status_code == 201
    user_uuid = create_user_response.json()["data"]["id"]

    upload_response = client.post(
        "/api/v1/statements/upload",
        data={"user_uuid": user_uuid},
        files={"file": ("income.csv", b"date,amount\n2026-07-01,300\n", "text/csv")},
    )
    assert upload_response.status_code == 201
    statement_uuid = upload_response.json()["data"]["statement_uuid"]

    with SessionLocal() as session:
        users = session.scalars(select(User)).all()
        statements = session.scalars(select(Statement)).all()

    assert len(users) == 1
    assert len(statements) == 1

    matched_users = [user for user in users if user.uuid == user_uuid]
    matched_statements = [statement for statement in statements if statement.uuid == statement_uuid]

    assert len(matched_users) == 1
    assert len(matched_statements) == 1
    assert matched_statements[0].user_id == matched_users[0].id
