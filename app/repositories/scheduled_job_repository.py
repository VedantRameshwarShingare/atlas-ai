"""Repository for persistent scheduled-job operations."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scheduled_job import ScheduledJob
from app.repositories.base_repository import BaseRepository


class ScheduledJobRepository(BaseRepository[ScheduledJob]):
    """Repository for managing scheduled-job records."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, ScheduledJob)

    async def get_for_user(
        self,
        job_id: UUID,
        user_id: UUID,
    ) -> ScheduledJob | None:
        """Return a scheduled job owned by the given user."""

        statement = select(ScheduledJob).where(
            ScheduledJob.id == job_id,
            ScheduledJob.user_id == user_id,
        )

        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_for_user(
        self,
        user_id: UUID,
        *,
        enabled: bool | None = None,
    ) -> list[ScheduledJob]:
        """Return scheduled jobs belonging to a user."""

        statement = select(ScheduledJob).where(
            ScheduledJob.user_id == user_id,
        )

        if enabled is not None:
            statement = statement.where(
                ScheduledJob.enabled == enabled,
            )

        statement = statement.order_by(
            ScheduledJob.created_at.desc(),
            ScheduledJob.id,
        )

        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def list_for_workspace(
        self,
        workspace_id: UUID,
        *,
        enabled: bool | None = None,
    ) -> list[ScheduledJob]:
        """Return scheduled jobs belonging to a workspace."""

        statement = select(ScheduledJob).where(
            ScheduledJob.workspace_id == workspace_id,
        )

        if enabled is not None:
            statement = statement.where(
                ScheduledJob.enabled == enabled,
            )

        statement = statement.order_by(
            ScheduledJob.created_at.desc(),
            ScheduledJob.id,
        )

        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def list_due(
        self,
        *,
        now: datetime,
        limit: int = 100,
    ) -> list[ScheduledJob]:
        """Return enabled jobs whose next execution time is due."""

        if limit <= 0:
            return []

        statement = (
            select(ScheduledJob)
            .where(
                ScheduledJob.enabled.is_(True),
                ScheduledJob.next_run_at.is_not(None),
                ScheduledJob.next_run_at <= now,
            )
            .order_by(
                ScheduledJob.next_run_at.asc(),
                ScheduledJob.id,
            )
            .limit(limit)
        )

        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def set_enabled(
        self,
        job_id: UUID,
        user_id: UUID,
        *,
        enabled: bool,
    ) -> ScheduledJob | None:
        """Enable or disable a user-owned scheduled job."""

        job = await self.get_for_user(job_id, user_id)

        if job is None:
            return None

        job.enabled = enabled
        await self.session.flush()

        return job

    async def update_run_state(
        self,
        job_id: UUID,
        *,
        last_run_at: datetime | None = None,
        next_run_at: datetime | None = None,
        last_error: str | None = None,
    ) -> ScheduledJob | None:
        """Update execution state for a scheduled job."""

        result = await self.session.execute(
            select(ScheduledJob).where(
                ScheduledJob.id == job_id,
            )
        )

        job = result.scalar_one_or_none()

        if job is None:
            return None

        if last_run_at is not None:
            job.last_run_at = last_run_at

        if next_run_at is not None:
            job.next_run_at = next_run_at

        job.last_error = last_error

        await self.session.flush()

        return job
