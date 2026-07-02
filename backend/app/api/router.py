"""API router composition and versioning."""

from __future__ import annotations

from fastapi import APIRouter

from backend.app.routers.statements import router as statements_router
from backend.app.routers.users import router as users_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(users_router)
api_router.include_router(statements_router)
