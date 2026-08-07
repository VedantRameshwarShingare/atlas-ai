"""Workspace endpoints for the API layer."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.api.responses import APIResponse

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.get("", response_model=APIResponse)
async def list_workspaces() -> APIResponse:
    """List available workspaces without business logic."""
    return APIResponse(data={"workspaces": []})


@router.post("", response_model=APIResponse)
async def create_workspace() -> APIResponse:
    """Create a workspace placeholder response."""
    return APIResponse(data={"status": "created", "workspace_id": "workspace-1"})


@router.get("/{workspace_id}", response_model=APIResponse)
async def get_workspace(workspace_id: str) -> APIResponse:
    """Return workspace metadata."""
    return APIResponse(data={"workspace_id": workspace_id, "status": "metadata_only"})


@router.delete("/{workspace_id}", response_model=APIResponse)
async def delete_workspace(workspace_id: str) -> APIResponse:
    """Delete a workspace placeholder response."""
    return APIResponse(data={"workspace_id": workspace_id, "status": "deleted"})
