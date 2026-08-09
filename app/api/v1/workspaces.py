"""Workspace endpoints for the API layer."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import CurrentUserDependency
from app.api.responses import APIResponse
from app.database.session import get_async_session
from app.schemas.workspace import (
    AddMemberRequest,
    MembershipResponse,
    UpdateMemberRoleRequest,
    WorkspaceCreateRequest,
    WorkspaceResponse,
    WorkspaceUpdateRequest,
)
from app.services.workspace_service import (
    WorkspaceForbiddenError,
    WorkspaceNotFoundError,
    WorkspaceService,
    WorkspaceValidationError,
)

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


def _to_workspace_response(workspace: object) -> WorkspaceResponse:
    return WorkspaceResponse.model_validate(workspace)


def _to_membership_response(membership: object, *, email: str | None) -> MembershipResponse:
    return MembershipResponse(
        workspace_id=membership.workspace_id,
        user_id=membership.user_id,
        email=email,
        role=membership.role,
        created_at=membership.created_at,
        updated_at=membership.updated_at,
    )


def _handle_workspace_error(exc: Exception) -> HTTPException:
    if isinstance(exc, WorkspaceNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, WorkspaceForbiddenError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, WorkspaceValidationError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Workspace operation failed")


@router.get("", response_model=APIResponse)
async def list_workspaces(
    current_user: CurrentUserDependency,
    session: AsyncSession = Depends(get_async_session),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
) -> APIResponse:
    """List workspaces visible to the authenticated user."""
    workspaces = await WorkspaceService(session).list_workspaces(current_user.id, offset=offset, limit=limit)
    return APIResponse(
        data={"workspaces": [WorkspaceResponse.model_validate(item).model_dump(mode="json") for item in workspaces]}
    )


@router.post("", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    payload: WorkspaceCreateRequest,
    current_user: CurrentUserDependency,
    session: AsyncSession = Depends(get_async_session),
) -> APIResponse:
    """Create a workspace and assign the current user as owner."""
    workspace = await WorkspaceService(session).create_workspace(
        owner_id=current_user.id,
        name=payload.name,
        description=payload.description,
    )
    return APIResponse(data={"workspace": _to_workspace_response(workspace).model_dump(mode="json")})


@router.get("/{workspace_id}", response_model=APIResponse)
async def get_workspace(
    workspace_id: UUID,
    current_user: CurrentUserDependency,
    session: AsyncSession = Depends(get_async_session),
) -> APIResponse:
    """Return workspace metadata for a member."""
    service = WorkspaceService(session)
    try:
        workspace = await service.get_workspace(workspace_id=workspace_id, user_id=current_user.id)
    except Exception as exc:
        raise _handle_workspace_error(exc) from exc
    return APIResponse(data={"workspace": _to_workspace_response(workspace).model_dump(mode="json")})


@router.patch("/{workspace_id}", response_model=APIResponse)
async def update_workspace(
    workspace_id: UUID,
    payload: WorkspaceUpdateRequest,
    current_user: CurrentUserDependency,
    session: AsyncSession = Depends(get_async_session),
) -> APIResponse:
    """Update workspace metadata for admin/owner members."""
    service = WorkspaceService(session)
    try:
        workspace = await service.update_workspace(
            workspace_id=workspace_id,
            user_id=current_user.id,
            name=payload.name,
            description=payload.description,
        )
    except Exception as exc:
        raise _handle_workspace_error(exc) from exc
    return APIResponse(data={"workspace": _to_workspace_response(workspace).model_dump(mode="json")})


@router.delete("/{workspace_id}", response_model=APIResponse)
async def delete_workspace(
    workspace_id: UUID,
    current_user: CurrentUserDependency,
    session: AsyncSession = Depends(get_async_session),
) -> APIResponse:
    """Delete a workspace when caller is owner."""
    service = WorkspaceService(session)
    try:
        await service.delete_workspace(workspace_id=workspace_id, user_id=current_user.id)
    except Exception as exc:
        raise _handle_workspace_error(exc) from exc
    return APIResponse(data={"workspace_id": str(workspace_id), "status": "deleted"})


@router.get("/{workspace_id}/members", response_model=APIResponse)
async def list_members(
    workspace_id: UUID,
    current_user: CurrentUserDependency,
    session: AsyncSession = Depends(get_async_session),
) -> APIResponse:
    """List workspace members for any workspace member."""
    service = WorkspaceService(session)
    try:
        memberships = await service.list_members(workspace_id=workspace_id, user_id=current_user.id)
    except Exception as exc:
        raise _handle_workspace_error(exc) from exc

    members = [
        _to_membership_response(membership, email=user.email).model_dump(mode="json")
        for membership, user in memberships
    ]
    return APIResponse(data={"members": members})


@router.post("/{workspace_id}/members", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def add_member(
    workspace_id: UUID,
    payload: AddMemberRequest,
    current_user: CurrentUserDependency,
    session: AsyncSession = Depends(get_async_session),
) -> APIResponse:
    """Add a user to workspace with role checks."""
    service = WorkspaceService(session)
    try:
        membership = await service.add_member(
            workspace_id=workspace_id,
            acting_user_id=current_user.id,
            email=str(payload.email),
            role=payload.role,
        )
        user = await service.users.get(membership.user_id)
    except Exception as exc:
        raise _handle_workspace_error(exc) from exc

    return APIResponse(
        data={
            "membership": _to_membership_response(
                membership, email=user.email if user is not None else None
            ).model_dump(mode="json")
        }
    )


@router.patch("/{workspace_id}/members/{member_user_id}", response_model=APIResponse)
async def update_member_role(
    workspace_id: UUID,
    member_user_id: UUID,
    payload: UpdateMemberRoleRequest,
    current_user: CurrentUserDependency,
    session: AsyncSession = Depends(get_async_session),
) -> APIResponse:
    """Update a member role with owner safety guarantees."""
    service = WorkspaceService(session)
    try:
        membership = await service.update_member_role(
            workspace_id=workspace_id,
            acting_user_id=current_user.id,
            target_user_id=member_user_id,
            role=payload.role,
        )
        user = await service.users.get(membership.user_id)
    except Exception as exc:
        raise _handle_workspace_error(exc) from exc

    return APIResponse(
        data={
            "membership": _to_membership_response(
                membership, email=user.email if user is not None else None
            ).model_dump(mode="json")
        }
    )


@router.delete("/{workspace_id}/members/{member_user_id}", response_model=APIResponse)
async def remove_member(
    workspace_id: UUID,
    member_user_id: UUID,
    current_user: CurrentUserDependency,
    session: AsyncSession = Depends(get_async_session),
) -> APIResponse:
    """Remove a workspace member with owner protection rules."""
    service = WorkspaceService(session)
    try:
        await service.remove_member(
            workspace_id=workspace_id,
            acting_user_id=current_user.id,
            target_user_id=member_user_id,
        )
    except Exception as exc:
        raise _handle_workspace_error(exc) from exc

    return APIResponse(data={"workspace_id": str(workspace_id), "user_id": str(member_user_id), "status": "removed"})
