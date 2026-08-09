"""Persistent scheduled-job API endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import CurrentUserDependency
from app.api.responses import APIResponse
from app.database.session import get_async_session
from app.schemas.scheduled_job import (
    ScheduledJobCreateRequest,
    ScheduledJobResponse,
    ScheduledJobUpdateRequest,
)
from app.services.scheduler.scheduler_service import (
    InvalidScheduleError,
    ScheduledJobNotFoundError,
    SchedulerService,
)
from app.services.workspace_service import (
    WorkspaceForbiddenError,
    WorkspaceNotFoundError,
    WorkspaceService,
)

router = APIRouter(
    prefix="/workspaces/{workspace_id}/scheduled-jobs",
    tags=["scheduled-jobs"],
)


def _handle_error(exc: Exception) -> HTTPException:
    """Convert scheduler domain errors into HTTP errors."""

    if isinstance(exc, ScheduledJobNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    if isinstance(exc, InvalidScheduleError):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Scheduled job operation failed",
    )


async def _require_workspace_member(
    *,
    workspace_id: UUID,
    user_id: UUID,
    session: AsyncSession,
) -> None:
    """Require the caller to be a member of the workspace."""

    try:
        await WorkspaceService(session).get_workspace(
            workspace_id=workspace_id,
            user_id=user_id,
        )
    except WorkspaceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except WorkspaceForbiddenError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc


def _to_response(job: object) -> ScheduledJobResponse:
    """Convert ORM job to API response."""

    return ScheduledJobResponse.model_validate(job)


@router.post(
    "",
    response_model=APIResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_scheduled_job(
    workspace_id: UUID,
    payload: ScheduledJobCreateRequest,
    current_user: CurrentUserDependency,
    session: AsyncSession = Depends(get_async_session),
) -> APIResponse:
    """Create a workspace-scoped scheduled job."""

    await _require_workspace_member(
        workspace_id=workspace_id,
        user_id=current_user.id,
        session=session,
    )

    service = SchedulerService(session)

    try:
        job = await service.create_job(
            user_id=current_user.id,
            workspace_id=workspace_id,
            name=payload.name,
            job_type=payload.job_type,
            schedule=payload.schedule,
            timezone=payload.timezone,
            enabled=payload.enabled,
            payload=payload.payload,
        )
    except Exception as exc:
        raise _handle_error(exc) from exc

    return APIResponse(
        data={
            "scheduled_job": _to_response(job).model_dump(mode="json"),
        }
    )


@router.get(
    "",
    response_model=APIResponse,
)
async def list_scheduled_jobs(
    workspace_id: UUID,
    current_user: CurrentUserDependency,
    session: AsyncSession = Depends(get_async_session),
) -> APIResponse:
    """List scheduled jobs belonging to a workspace."""

    await _require_workspace_member(
        workspace_id=workspace_id,
        user_id=current_user.id,
        session=session,
    )

    service = SchedulerService(session)
    jobs = await service.list_workspace_jobs(
        workspace_id=workspace_id,
    )

    return APIResponse(data={"scheduled_jobs": [_to_response(job).model_dump(mode="json") for job in jobs]})


@router.get(
    "/{job_id}",
    response_model=APIResponse,
)
async def get_scheduled_job(
    workspace_id: UUID,
    job_id: UUID,
    current_user: CurrentUserDependency,
    session: AsyncSession = Depends(get_async_session),
) -> APIResponse:
    """Return one scheduled job belonging to the workspace."""

    await _require_workspace_member(
        workspace_id=workspace_id,
        user_id=current_user.id,
        session=session,
    )

    service = SchedulerService(session)

    try:
        job = await service.get_job(
            user_id=current_user.id,
            job_id=job_id,
        )
    except Exception as exc:
        raise _handle_error(exc) from exc

    if job.workspace_id != workspace_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheduled job not found",
        )

    return APIResponse(
        data={
            "scheduled_job": _to_response(job).model_dump(mode="json"),
        }
    )


@router.patch(
    "/{job_id}",
    response_model=APIResponse,
)
async def update_scheduled_job(
    workspace_id: UUID,
    job_id: UUID,
    payload: ScheduledJobUpdateRequest,
    current_user: CurrentUserDependency,
    session: AsyncSession = Depends(get_async_session),
) -> APIResponse:
    """Update a workspace scheduled job."""

    await _require_workspace_member(
        workspace_id=workspace_id,
        user_id=current_user.id,
        session=session,
    )

    service = SchedulerService(session)

    try:
        existing = await service.get_job(
            user_id=current_user.id,
            job_id=job_id,
        )

        if existing.workspace_id != workspace_id:
            raise ScheduledJobNotFoundError(f"Scheduled job {job_id} was not found.")

        job = await service.update_job(
            user_id=current_user.id,
            job_id=job_id,
            name=payload.name,
            schedule=payload.schedule,
            timezone=payload.timezone,
            enabled=payload.enabled,
            payload=payload.payload,
        )
    except Exception as exc:
        raise _handle_error(exc) from exc

    return APIResponse(
        data={
            "scheduled_job": _to_response(job).model_dump(mode="json"),
        }
    )


@router.delete(
    "/{job_id}",
    response_model=APIResponse,
)
async def delete_scheduled_job(
    workspace_id: UUID,
    job_id: UUID,
    current_user: CurrentUserDependency,
    session: AsyncSession = Depends(get_async_session),
) -> APIResponse:
    """Delete a workspace scheduled job."""

    await _require_workspace_member(
        workspace_id=workspace_id,
        user_id=current_user.id,
        session=session,
    )

    service = SchedulerService(session)

    try:
        job = await service.get_job(
            user_id=current_user.id,
            job_id=job_id,
        )

        if job.workspace_id != workspace_id:
            raise ScheduledJobNotFoundError(f"Scheduled job {job_id} was not found.")

        await service.delete_job(
            user_id=current_user.id,
            job_id=job_id,
        )
    except Exception as exc:
        raise _handle_error(exc) from exc

    return APIResponse(
        data={
            "workspace_id": str(workspace_id),
            "job_id": str(job_id),
            "status": "deleted",
        }
    )


@router.post(
    "/{job_id}/enable",
    response_model=APIResponse,
)
async def enable_scheduled_job(
    workspace_id: UUID,
    job_id: UUID,
    current_user: CurrentUserDependency,
    session: AsyncSession = Depends(get_async_session),
) -> APIResponse:
    """Enable a workspace scheduled job."""

    await _require_workspace_member(
        workspace_id=workspace_id,
        user_id=current_user.id,
        session=session,
    )

    service = SchedulerService(session)

    try:
        existing = await service.get_job(
            user_id=current_user.id,
            job_id=job_id,
        )

        if existing.workspace_id != workspace_id:
            raise ScheduledJobNotFoundError(f"Scheduled job {job_id} was not found.")

        job = await service.enable_job(
            user_id=current_user.id,
            job_id=job_id,
        )
    except Exception as exc:
        raise _handle_error(exc) from exc

    return APIResponse(
        data={
            "scheduled_job": _to_response(job).model_dump(mode="json"),
        }
    )


@router.post(
    "/{job_id}/disable",
    response_model=APIResponse,
)
async def disable_scheduled_job(
    workspace_id: UUID,
    job_id: UUID,
    current_user: CurrentUserDependency,
    session: AsyncSession = Depends(get_async_session),
) -> APIResponse:
    """Disable a workspace scheduled job."""

    await _require_workspace_member(
        workspace_id=workspace_id,
        user_id=current_user.id,
        session=session,
    )

    service = SchedulerService(session)

    try:
        existing = await service.get_job(
            user_id=current_user.id,
            job_id=job_id,
        )

        if existing.workspace_id != workspace_id:
            raise ScheduledJobNotFoundError(f"Scheduled job {job_id} was not found.")

        job = await service.disable_job(
            user_id=current_user.id,
            job_id=job_id,
        )
    except Exception as exc:
        raise _handle_error(exc) from exc

    return APIResponse(
        data={
            "scheduled_job": _to_response(job).model_dump(mode="json"),
        }
    )
