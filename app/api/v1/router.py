"""Version-one API router composition."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.auth.router import router as auth_router
from app.api.v1.chat import router as chat_router
from app.api.v1.documents import router as documents_router
from app.api.v1.finance import router as finance_router
from app.api.v1.health import router as health_router
from app.api.v1.scheduled_jobs import router as scheduled_jobs_router
from app.api.v1.telegram import router as telegram_router
from app.api.v1.workspaces import router as workspaces_router

v1_router = APIRouter()

v1_router.include_router(health_router)
v1_router.include_router(auth_router)
v1_router.include_router(chat_router)
v1_router.include_router(workspaces_router)
v1_router.include_router(documents_router)
v1_router.include_router(finance_router)
v1_router.include_router(telegram_router)
v1_router.include_router(scheduled_jobs_router)

__all__ = ["v1_router"]
