"""API router composition and versioning."""

from __future__ import annotations

from fastapi import APIRouter

from backend.app.routers.ai import router as ai_router
from backend.app.routers.assistant import router as assistant_router
from backend.app.routers.statements import router as statements_router
from backend.app.routers.transactions import router as transactions_router
from backend.app.routers.users import router as users_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(ai_router)
api_router.include_router(assistant_router)
api_router.include_router(users_router)
api_router.include_router(statements_router)
api_router.include_router(transactions_router)
