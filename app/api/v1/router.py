"""Version 1 API router."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.api.v1.chat import router as chat_router
from app.api.v1.documents import router as documents_router
from app.api.v1.workspaces import router as workspaces_router
from app.api.v1.watchlists import router as watchlists_router
from app.api.v1.alerts import router as alerts_router
from app.api.v1.users import router as users_router

v1_router = APIRouter()
v1_router.include_router(health_router)
v1_router.include_router(chat_router)
v1_router.include_router(documents_router)
v1_router.include_router(workspaces_router)
v1_router.include_router(watchlists_router)
v1_router.include_router(alerts_router)
v1_router.include_router(users_router)
