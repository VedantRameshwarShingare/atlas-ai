"""Health endpoint for the API layer."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Request

from app.api.responses import APIResponse
from app.config import settings

router = APIRouter(tags=["health"])


@router.get("/health", response_model=APIResponse)
async def health(request: Request) -> APIResponse:
    """Return service status and environment information."""
    return APIResponse(
        data={
            "status": "ok",
            "version": settings.project_version,
            "environment": settings.environment,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        request_id=getattr(request.state, "request_id", None),
    )
