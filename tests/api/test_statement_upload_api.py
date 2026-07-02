from __future__ import annotations

from decimal import Decimal

from fastapi.testclient import TestClient

from backend.app.database.init_db import init_database
from backend.app.database.session import create_database_engine, create_session_factory
from backend.app.main import create_app
from backend.app.models.user import User
from walletmind.services.statement_upload_service import StatementUploadService


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
    assert body["statement_uuid"]
    assert body["original_filename"] == "june.csv"
    assert body["file_type"] == "csv"
    assert body["analysis_status"] == "uploaded"
    assert body["status"] == "uploaded"


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
    assert isinstance(body, list)
    assert len(body) == 1
    assert body[0]["original_filename"] == "june.csv"


def test_statement_get_endpoint(tmp_path) -> None:
    client, session_factory = _setup_client_with_statement_service(tmp_path)
    user = _create_persisted_user(session_factory)

    upload_response = client.post(
        "/api/v1/statements/upload",
        data={"user_uuid": user.uuid},
        files={"file": ("july.xlsx", b"PK\x03\x04xlsx-content", "application/vnd.ms-excel")},
    )
    statement_uuid = upload_response.json()["statement_uuid"]

    response = client.get(f"/api/v1/statements/{statement_uuid}")

    assert response.status_code == 200
    body = response.json()
    assert body["statement_uuid"] == statement_uuid
    assert body["original_filename"] == "july.xlsx"


def test_statement_delete_endpoint(tmp_path) -> None:
    client, session_factory = _setup_client_with_statement_service(tmp_path)
    user = _create_persisted_user(session_factory)

    upload_response = client.post(
        "/api/v1/statements/upload",
        data={"user_uuid": user.uuid},
        files={"file": ("aug.csv", b"date,amount\n2026-08-01,200\n", "text/csv")},
    )
    body = upload_response.json()
    statement_uuid = body["statement_uuid"]
    stored_filename = body["stored_filename"]

    delete_response = client.delete(f"/api/v1/statements/{statement_uuid}")

    assert delete_response.status_code == 204
    assert not (tmp_path / "uploads" / stored_filename).exists()

    get_response = client.get(f"/api/v1/statements/{statement_uuid}")
    assert get_response.status_code == 404
    assert get_response.json()["code"] == "STATEMENT_NOT_FOUND"
