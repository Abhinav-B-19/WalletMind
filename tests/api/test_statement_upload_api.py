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
from walletmind.services.processing_dispatcher import ProcessingDispatcher
from walletmind.services.statement_processing_service import StatementProcessingService
from walletmind.services.statement_upload_service import StatementUploadService
from walletmind.services.transaction_service import TransactionService
from walletmind.services.user_service import UserService


@pytest.fixture(autouse=True)
def _reset_database() -> None:
    with SessionLocal() as session:
        session.execute(delete(Statement))
        session.execute(delete(User))
        session.commit()


def _setup_client_with_statement_service(tmp_path, processing_dispatcher: ProcessingDispatcher | None = None):
    database_url = f"sqlite+pysqlite:///{(tmp_path / 'api-test.db').as_posix()}"
    database_engine = create_database_engine(database_url)
    session_factory = create_session_factory(database_engine)
    init_database(database_engine)

    app = create_app()
    app.state.user_service = UserService(session_factory=session_factory)
    app.state.statement_upload_service = StatementUploadService(
        session_factory=session_factory,
        upload_dir=tmp_path / "uploads",
    )
    app.state.statement_processing_service = StatementProcessingService(
        session_factory=session_factory,
    )
    app.state.transaction_service = TransactionService(session_factory=session_factory)
    app.state.processing_dispatcher = processing_dispatcher or ProcessingDispatcher(
        processing_service=app.state.statement_processing_service,
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
        files={
            "file": (
                "june.csv",
                b"Date,Narration,Withdrawal,Deposit\n2026-06-01,Salary,0,120\n",
                "text/csv",
            )
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "Statement uploaded successfully."
    assert body["data"]["statement_uuid"]
    assert body["data"]["original_filename"] == "june.csv"
    assert body["data"]["file_type"] == "csv"
    assert body["data"]["analysis_status"] == "ready_for_analysis"
    assert body["data"]["status"] == "ready_for_analysis"
    assert body["data"]["parsed_transaction_count"] >= 1
    assert body["data"]["failed_transaction_count"] >= 0
    assert body["data"]["parsed_at"] is not None
    assert body["data"]["classification_confidence"] is not None
    assert body["data"]["classification_method"] is not None
    assert body["data"]["classified_at"] is not None


def test_statement_list_endpoint(tmp_path) -> None:
    client, session_factory = _setup_client_with_statement_service(tmp_path)
    user = _create_persisted_user(session_factory)

    client.post(
        "/api/v1/statements/upload",
        data={"user_uuid": user.uuid},
        files={
            "file": (
                "june.csv",
                b"Date,Narration,Withdrawal,Deposit\n2026-06-01,Salary,0,120\n",
                "text/csv",
            )
        },
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
        files={
            "file": (
                "u1.csv",
                b"Date,Narration,Withdrawal,Deposit\n2026-06-01,Salary,0,120\n",
                "text/csv",
            )
        },
    )
    client.post(
        "/api/v1/statements/upload",
        data={"user_uuid": user_two.uuid},
        files={
            "file": (
                "u2.csv",
                b"Date,Narration,Withdrawal,Deposit\n2026-06-01,Salary,0,220\n",
                "text/csv",
            )
        },
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
        files={
            "file": (
                "workflow.csv",
                b"Date,Narration,Withdrawal,Deposit\n2026-08-01,Salary,0,500\n",
                "text/csv",
            )
        },
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
        files={
            "file": (
                "aug.csv",
                b"Date,Narration,Withdrawal,Deposit\n2026-08-01,Salary,0,200\n",
                "text/csv",
            )
        },
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


def test_create_user_then_upload_statement_uses_same_database(tmp_path) -> None:
    client, session_factory = _setup_client_with_statement_service(tmp_path)

    create_user_response = client.post(
        "/api/v1/users",
        json={
            "name": "Jordan Blake",
            "occupation": "Analyst",
            "monthly_income": 6100,
            "currency": "USD",
            "primary_financial_goal": "Build Emergency Fund",
        },
    )
    assert create_user_response.status_code == 201
    user_uuid = create_user_response.json()["data"]["id"]

    upload_response = client.post(
        "/api/v1/statements/upload",
        data={"user_uuid": user_uuid},
        files={
            "file": (
                "income.csv",
                b"Date,Narration,Withdrawal,Deposit\n2026-07-01,Salary,0,300\n",
                "text/csv",
            )
        },
    )
    assert upload_response.status_code == 201
    statement_uuid = upload_response.json()["data"]["statement_uuid"]

    with session_factory() as session:
        users = session.scalars(select(User)).all()
        statements = session.scalars(select(Statement)).all()

    assert len(users) == 1
    assert len(statements) == 1

    matched_users = [user for user in users if user.uuid == user_uuid]
    matched_statements = [statement for statement in statements if statement.uuid == statement_uuid]

    assert len(matched_users) == 1
    assert len(matched_statements) == 1
    assert matched_statements[0].user_id == matched_users[0].id


def test_upload_pipeline_transitions_to_ready_for_analysis(tmp_path) -> None:
    client, session_factory = _setup_client_with_statement_service(tmp_path)
    user = _create_persisted_user(session_factory)

    response = client.post(
        "/api/v1/statements/upload",
        data={"user_uuid": user.uuid},
        files={
            "file": (
                "pipeline.csv",
                b"Date,Narration,Withdrawal,Deposit\n2026-06-01,Salary,0,120\n",
                "text/csv",
            )
        },
    )

    assert response.status_code == 201
    statement_uuid = response.json()["data"]["statement_uuid"]
    assert response.json()["data"]["status"] == "ready_for_analysis"

    with session_factory() as session:
        statement = session.scalar(select(Statement).where(Statement.uuid == statement_uuid))

    assert statement is not None
    assert statement.status.value == "ready_for_analysis"
    assert statement.detected_file_type == "csv"
    assert statement.parser_type is not None
    assert statement.processing_started_at is not None
    assert statement.processing_completed_at is not None
    assert statement.classification_confidence is not None
    assert statement.classification_method is not None
    assert statement.classified_at is not None
    assert statement.parsed_transaction_count >= 1
    assert statement.failed_transaction_count >= 0
    assert statement.parsed_at is not None


def test_upload_dispatches_processing_via_dispatcher(tmp_path) -> None:
    class _SpyDispatcher:
        def __init__(self) -> None:
            self.calls: list[dict[str, str | None]] = []

        def dispatch(
            self,
            *,
            background_tasks,
            statement_uuid,
            original_filename: str,
            stored_file_path: str,
            content_type: str | None = None,
        ) -> None:
            self.calls.append(
                {
                    "statement_uuid": str(statement_uuid),
                    "original_filename": original_filename,
                    "stored_file_path": stored_file_path,
                    "content_type": content_type,
                }
            )

    spy_dispatcher = _SpyDispatcher()
    client, session_factory = _setup_client_with_statement_service(
        tmp_path,
        processing_dispatcher=spy_dispatcher,
    )
    user = _create_persisted_user(session_factory)

    response = client.post(
        "/api/v1/statements/upload",
        data={"user_uuid": user.uuid},
        files={
            "file": (
                "dispatch.csv",
                b"Date,Narration,Withdrawal,Deposit\n2026-06-01,Salary,0,120\n",
                "text/csv",
            )
        },
    )

    assert response.status_code == 201
    assert len(spy_dispatcher.calls) == 1
    assert spy_dispatcher.calls[0]["original_filename"] == "dispatch.csv"
    assert spy_dispatcher.calls[0]["content_type"] == "text/csv"
    assert spy_dispatcher.calls[0]["stored_file_path"]


def test_upload_axis_statement_classified_with_axis_parser(tmp_path) -> None:
    client, session_factory = _setup_client_with_statement_service(tmp_path)
    user = _create_persisted_user(session_factory)

    response = client.post(
        "/api/v1/statements/upload",
        data={"user_uuid": user.uuid},
        files={
            "file": (
                "axis_statement.csv",
                b"Tran Date,CHQNO,PARTICULARS,DR,CR,BAL,SOL\n2026-07-01,-,Salary,0,10000,10000,014\n",
                "text/csv",
            )
        },
    )

    assert response.status_code == 201
    body = response.json()["data"]
    assert body["bank_name"] == "Axis Bank"
    assert body["parser_type"] == "csv_parser"
    assert body["status"] == "ready_for_analysis"


def test_upload_tmb_statement_classified_with_tmb_parser(tmp_path) -> None:
    client, session_factory = _setup_client_with_statement_service(tmp_path)
    user = _create_persisted_user(session_factory)

    response = client.post(
        "/api/v1/statements/upload",
        data={"user_uuid": user.uuid},
        files={
            "file": (
                "tmb_statement.csv",
                b"Date,Narration,Withdrawal,Deposit\n2026-07-01,ATM,200,0\n",
                "text/csv",
            )
        },
    )

    assert response.status_code == 201
    body = response.json()["data"]
    assert body["bank_name"] == "Tamilnad Mercantile Bank"
    assert body["parser_type"] == "csv_parser"


def test_upload_canara_statement_classified_with_canara_parser(tmp_path) -> None:
    client, session_factory = _setup_client_with_statement_service(tmp_path)
    user = _create_persisted_user(session_factory)

    response = client.post(
        "/api/v1/statements/upload",
        data={"user_uuid": user.uuid},
        files={
            "file": (
                "canara_statement.csv",
                b"Txn Date,Description,Debit,Credit,Balance\n2026-07-01,UPI,200,0,900\n",
                "text/csv",
            )
        },
    )

    assert response.status_code == 201
    body = response.json()["data"]
    assert body["bank_name"] == "Canara Bank"
    assert body["parser_type"] == "csv_parser"


def test_upload_unknown_statement_classified_with_generic_parser(tmp_path) -> None:
    client, session_factory = _setup_client_with_statement_service(tmp_path)
    user = _create_persisted_user(session_factory)

    response = client.post(
        "/api/v1/statements/upload",
        data={"user_uuid": user.uuid},
        files={
            "file": (
                "unknown_statement.csv",
                b"col1,col2,col3\n1,2,3\n",
                "text/csv",
            )
        },
    )

    assert response.status_code == 201
    body = response.json()["data"]
    assert body["bank_name"] == "Unknown"
    assert body["parser_type"] == "csv_parser"
    assert body["status"] == "parse_failed"
