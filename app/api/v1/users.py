"""User endpoints for the API layer."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import AuthenticatedUserDependency
from app.api.responses import APIResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=APIResponse)
async def get_me(user: AuthenticatedUserDependency) -> APIResponse:
    """Return the authenticated user placeholder profile."""
    return APIResponse(data={"user": user})


@router.patch("/me/preferences", response_model=APIResponse)
async def update_preferences(user: AuthenticatedUserDependency) -> APIResponse:
    """Update preferences placeholder response."""
    return APIResponse(data={"user": user, "status": "preferences_updated"})
