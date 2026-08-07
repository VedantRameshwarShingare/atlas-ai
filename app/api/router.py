"""Root router composition for the minimal HTTP API."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.router import v1_router

api_router = APIRouter()
api_router.include_router(v1_router)

__all__ = ["api_router"]
