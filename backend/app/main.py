"""FastAPI entry point for WalletMind backend."""

from __future__ import annotations

import sys
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def _ensure_project_root_on_path() -> None:
    """Add the project root to Python's import path for direct script execution."""

    project_root = Path(__file__).resolve().parents[2]
    project_root_path = str(project_root)
    if project_root_path not in sys.path:
        sys.path.insert(0, project_root_path)


_ensure_project_root_on_path()

from backend.app.api.errors import register_error_handlers
from backend.app.api.router import api_router
from backend.app.core.config import STORAGE_DIR
from backend.app.database.init_db import init_database
from backend.app.database.session import SessionLocal
from walletmind.services.statement_upload_service import StatementUploadService
from walletmind.services.user_service import UserService


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title="WalletMind User Registration API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    init_database()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.user_service = UserService()
    app.state.statement_upload_service = StatementUploadService(
        session_factory=SessionLocal,
        upload_dir=STORAGE_DIR / "uploads",
    )
    app.include_router(api_router)
    register_error_handlers(app)

    return app


app = create_app()


def main() -> int:
    """Run the WalletMind FastAPI server."""

    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
