"""Version-one API router composition."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.health import router as health_router

v1_router = APIRouter()
v1_router.include_router(health_router)

__all__ = ["v1_router"]
