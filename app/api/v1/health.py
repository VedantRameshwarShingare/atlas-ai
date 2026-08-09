"""Minimal health endpoint for infrastructure checks."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.database.health import is_database_connected

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Health-check response payload."""

    status: str
    database: str


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Report HTTP and database readiness without exposing connection details."""

    if await is_database_connected():
        return HealthResponse(
            status="healthy",
            database="connected",
        )

    return HealthResponse(
        status="unhealthy",
        database="unavailable",
    )
