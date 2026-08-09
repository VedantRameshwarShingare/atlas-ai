"""Business service for persistent Atlas scheduled jobs."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo

from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scheduled_job import ScheduledJob, ScheduledJobType
from app.repositories.scheduled_job_repository import ScheduledJobRepository
from app.scheduler.manager import SchedulerManager


class SchedulerServiceError(Exception):
    """Base exception for scheduler-service failures."""


class ScheduledJobNotFoundError(SchedulerServiceError):
    """Raised when a scheduled job cannot be found for the current user."""


class InvalidScheduleError(SchedulerServiceError):
    """Raised when a schedule or timezone is invalid."""


class SchedulerService:
    """Manage persistent scheduled jobs and their business rules."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        scheduler_manager: SchedulerManager | None = None,
    ) -> None:
        self.repository = ScheduledJobRepository(session)
        self.scheduler_manager = scheduler_manager

    async def create_job(
        self,
        *,
        user_id: UUID,
        name: str,
        job_type: ScheduledJobType | str,
        schedule: str,
        timezone: str = "UTC",
        enabled: bool = True,
        payload: dict | None = None,
        workspace_id: UUID | None = None,
    ) -> ScheduledJob:
        """Create a validated persistent scheduled job."""

        normalized_name = name.strip()
        normalized_schedule = schedule.strip()

        if not normalized_name:
            raise ValueError("Scheduled job name cannot be blank.")

        if len(normalized_name) > 255:
            raise ValueError("Scheduled job name cannot exceed 255 characters.")

        if not normalized_schedule:
            raise InvalidScheduleError("Schedule cannot be blank.")

        normalized_timezone = self._validate_timezone(timezone)
        normalized_job_type = self._validate_job_type(job_type)

        self._validate_schedule(
            normalized_schedule,
            normalized_timezone,
        )

        job = ScheduledJob(
            user_id=user_id,
            workspace_id=workspace_id,
            name=normalized_name,
            job_type=normalized_job_type,
            schedule=normalized_schedule,
            timezone=normalized_timezone,
            enabled=enabled,
            payload=payload or {},
        )

        job = await self.repository.create(job)

        self.register_runtime_job(job)

        return job

    async def get_job(
        self,
        *,
        user_id: UUID,
        job_id: UUID,
    ) -> ScheduledJob:
        """Return a scheduled job owned by the current user."""

        job = await self.repository.get_for_user(
            job_id,
            user_id,
        )

        if job is None:
            raise ScheduledJobNotFoundError(f"Scheduled job {job_id} was not found.")

        return job

    async def list_jobs(
        self,
        *,
        user_id: UUID,
        enabled: bool | None = None,
    ) -> list[ScheduledJob]:
        """List scheduled jobs owned by the current user."""

        return await self.repository.list_for_user(
            user_id,
            enabled=enabled,
        )

    async def list_workspace_jobs(
        self,
        *,
        workspace_id: UUID,
        enabled: bool | None = None,
    ) -> list[ScheduledJob]:
        """List scheduled jobs belonging to a workspace."""

        return await self.repository.list_for_workspace(
            workspace_id,
            enabled=enabled,
        )

    async def update_job(
        self,
        *,
        user_id: UUID,
        job_id: UUID,
        name: str | None = None,
        schedule: str | None = None,
        timezone: str | None = None,
        enabled: bool | None = None,
        payload: dict | None = None,
        workspace_id: UUID | None = None,
        update_workspace: bool = False,
    ) -> ScheduledJob:
        """Update a user-owned scheduled job."""

        job = await self.get_job(
            user_id=user_id,
            job_id=job_id,
        )

        if name is not None:
            normalized_name = name.strip()

            if not normalized_name:
                raise ValueError("Scheduled job name cannot be blank.")

            if len(normalized_name) > 255:
                raise ValueError("Scheduled job name cannot exceed 255 characters.")

            job.name = normalized_name

        if timezone is not None:
            job.timezone = self._validate_timezone(timezone)

        if schedule is not None:
            normalized_schedule = schedule.strip()

            if not normalized_schedule:
                raise InvalidScheduleError("Schedule cannot be blank.")

            job.schedule = normalized_schedule

        if schedule is not None or timezone is not None:
            self._validate_schedule(
                job.schedule,
                job.timezone,
            )

        if enabled is not None:
            job.enabled = enabled

        if payload is not None:
            job.payload = payload

        if update_workspace:
            job.workspace_id = workspace_id

        job = await self.repository.update(job)

        self.register_runtime_job(job)

        return job

    async def delete_job(
        self,
        *,
        user_id: UUID,
        job_id: UUID,
    ) -> None:
        """Delete a user-owned scheduled job."""

        job = await self.get_job(
            user_id=user_id,
            job_id=job_id,
        )

        if self.scheduler_manager is not None:
            self.remove_runtime_job(job.id)

        await self.repository.delete(job)

    async def enable_job(
        self,
        *,
        user_id: UUID,
        job_id: UUID,
    ) -> ScheduledJob:
        """Enable a user-owned scheduled job."""

        job = await self.repository.set_enabled(
            job_id,
            user_id,
            enabled=True,
        )

        if job is None:
            raise ScheduledJobNotFoundError(f"Scheduled job {job_id} was not found.")

        self.register_runtime_job(job)

        return job

    async def disable_job(
        self,
        *,
        user_id: UUID,
        job_id: UUID,
    ) -> ScheduledJob:
        """Disable a user-owned scheduled job."""

        job = await self.repository.set_enabled(
            job_id,
            user_id,
            enabled=False,
        )

        if job is None:
            raise ScheduledJobNotFoundError(f"Scheduled job {job_id} was not found.")

        self.pause_runtime_job(job.id)

        return job

    async def record_run(
        self,
        *,
        job_id: UUID,
        last_run_at: datetime,
        next_run_at: datetime | None = None,
        last_error: str | None = None,
    ) -> ScheduledJob:
        """Persist the execution state of a scheduled job."""

        job = await self.repository.update_run_state(
            job_id,
            last_run_at=last_run_at,
            next_run_at=next_run_at,
            last_error=last_error,
        )

        if job is None:
            raise ScheduledJobNotFoundError(f"Scheduled job {job_id} was not found.")

        return job

    async def list_due_jobs(
        self,
        *,
        now: datetime,
        limit: int = 100,
    ) -> list[ScheduledJob]:
        """Return enabled jobs that are due for execution."""

        return await self.repository.list_due(
            now=now,
            limit=limit,
        )

    async def load_runtime_jobs(
        self,
        jobs: list[ScheduledJob],
    ) -> int:
        """
        Register persisted jobs with APScheduler during application startup.

        The caller supplies the persisted jobs so this service does not
        introduce another database-loading abstraction.
        """
        if self.scheduler_manager is None:
            return 0

        registered = 0

        for job in jobs:
            self.register_runtime_job(job)
            registered += 1

        return registered

    async def run_now(
        self,
        *,
        user_id: UUID,
        job_id: UUID,
    ) -> dict[str, Any]:
        """Execute a persistent scheduled job immediately."""

        job = await self.get_job(
            user_id=user_id,
            job_id=job_id,
        )

        worker = self._build_runtime_worker(job)

        started_at = datetime.now(UTC)

        try:
            result = worker.run(
                job_id=str(job.id),
                scheduled_at=started_at,
                metadata=job.payload.copy(),
            )

            if hasattr(result, "__await__"):
                result = await result

            await self.record_run(
                job_id=job.id,
                last_run_at=started_at,
                last_error=None,
            )

            return {
                "job_id": str(job.id),
                "status": "success",
                "started_at": started_at,
                "result": result,
            }

        except Exception as exc:
            await self.record_run(
                job_id=job.id,
                last_run_at=started_at,
                last_error=f"{type(exc).__name__}: {exc}",
            )
            raise

    @staticmethod
    def _validate_job_type(
        job_type: ScheduledJobType | str,
    ) -> str:
        """Validate and normalize the scheduled job type."""

        try:
            return ScheduledJobType(job_type).value
        except ValueError as exc:
            supported = ", ".join(job_type.value for job_type in ScheduledJobType)

            raise ValueError(f"Unsupported scheduled job type: {job_type}. Supported types: {supported}") from exc

    @staticmethod
    def _validate_timezone(timezone: str) -> str:
        """Validate an IANA timezone name."""

        normalized = timezone.strip()

        if not normalized:
            raise InvalidScheduleError("Timezone cannot be blank.")

        try:
            ZoneInfo(normalized)
        except Exception as exc:
            raise InvalidScheduleError(f"Invalid timezone: {normalized}") from exc

        return normalized

    @staticmethod
    def _validate_schedule(
        schedule: str,
        timezone: str,
    ) -> None:
        """Validate a cron schedule against its configured timezone."""

        try:
            CronTrigger.from_crontab(
                schedule,
                timezone=ZoneInfo(timezone),
            )
        except (ValueError, TypeError) as exc:
            raise InvalidScheduleError(f"Invalid cron schedule: {schedule}") from exc

    def _build_trigger(
        self,
        job: ScheduledJob,
    ) -> CronTrigger:
        """Build the trigger for a scheduled job."""

        return CronTrigger.from_crontab(
            job.schedule,
            timezone=ZoneInfo(job.timezone),
        )

    def _build_runtime_worker(
        self,
        job: ScheduledJob,
    ) -> Any:
        """Build the worker used by the persistent scheduler runtime."""

        if self.scheduler_manager is None:
            raise SchedulerServiceError("Scheduler manager is not configured.")

        capabilities = self.scheduler_manager.capabilities

        if capabilities is None:
            raise SchedulerServiceError("Scheduler capabilities are not configured.")

        from app.scheduler.workers.persistent import (
            PersistentJobWorker,
        )

        return PersistentJobWorker(
            job_type=job.job_type,
            payload=job.payload,
            capabilities=capabilities,
        )

    def register_runtime_job(
        self,
        job: ScheduledJob,
    ) -> None:
        """Register or replace a persistent job in APScheduler."""

        if self.scheduler_manager is None:
            return

        worker = self._build_runtime_worker(job)

        self.scheduler_manager.scheduler.add_job(
            worker.run,
            trigger=self._build_trigger(job),
            id=str(job.id),
            replace_existing=True,
        )

    def remove_runtime_job(
        self,
        job_id: UUID,
    ) -> None:
        """Remove a persistent job from APScheduler."""

        if self.scheduler_manager is None:
            return

        runtime_job = self.scheduler_manager.scheduler.get_job(
            str(job_id),
        )

        if runtime_job is not None:
            self.scheduler_manager.scheduler.remove_job(
                str(job_id),
            )

    def pause_runtime_job(
        self,
        job_id: UUID,
    ) -> None:
        """Pause a persistent job in APScheduler."""

        if self.scheduler_manager is None:
            return

        runtime_job = self.scheduler_manager.scheduler.get_job(
            str(job_id),
        )

        if runtime_job is not None:
            self.scheduler_manager.scheduler.pause_job(
                str(job_id),
            )
        else:
            return

    def resume_runtime_job(
        self,
        job: ScheduledJob,
    ) -> None:
        """Resume an existing persistent job in APScheduler."""

        if self.scheduler_manager is None:
            return

        runtime_job = self.scheduler_manager.scheduler.get_job(
            str(job.id),
        )

        if runtime_job is None:
            self.register_runtime_job(job)
            return

        self.scheduler_manager.scheduler.resume_job(
            str(job.id),
        )
