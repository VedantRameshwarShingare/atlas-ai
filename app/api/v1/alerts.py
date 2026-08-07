"""Alerts endpoints for the API layer."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.responses import APIResponse

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=APIResponse)
async def list_alerts() -> APIResponse:
    """List alerts without business logic."""
    return APIResponse(data={"alerts": []})


@router.post("", response_model=APIResponse)
async def create_alert() -> APIResponse:
    """Create an alert placeholder response."""
    return APIResponse(data={"status": "created"})


@router.delete("/{alert_id}", response_model=APIResponse)
async def delete_alert(alert_id: str) -> APIResponse:
    """Delete an alert placeholder response."""
    return APIResponse(data={"alert_id": alert_id, "status": "deleted"})
