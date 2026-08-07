"""APScheduler lifecycle and execution management for Atlas AI."""

from __future__ import annotations

import asyncio
import inspect
import logging
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.ai.capabilities import CapabilityRegistry
from app.scheduler.jobs.base import ScheduledJob
from app.scheduler.jobs.job_result import JobResult
from app.scheduler.registry import JobRegistry
from app.scheduler.scheduler import create_scheduler
from app.scheduler.triggers import build_cron_trigger, build_interval_trigger
from app.scheduler.workers import (
    AlertDispatcherWorker,
    DocumentProcessorWorker,
    EarningsMonitorWorker,
    HealthCheckWorker,
    MarketMonitorWorker,
    MorningBriefWorker,
    WatchlistMonitorWorker,
    WorkspaceCleanupWorker,
)

logger = logging.getLogger("atlas_ai.scheduler")


class SchedulerManager:
    """Own scheduler lifecycle, job registration, retries, and job observability."""

    def __init__(
        self,
        *,
        scheduler: AsyncIOScheduler | None = None,
        registry: JobRegistry | None = None,
        timezone_name: str = "UTC",
    ) -> None:
        self.timezone = ZoneInfo(timezone_name)
        self.scheduler = scheduler or create_scheduler(timezone_name=timezone_name)
        self.registry = registry or JobRegistry()
        self._started = False

    @property
    def running(self) -> bool:
        """Whether APScheduler has been started and has not been shut down."""
        return self._started and self.scheduler.running

    async def start(self) -> None:
        if self.scheduler.running:
            self._started = True
            return
        self.scheduler.start()
        self._started = True
        logger.info("scheduler_started", extra={"timezone": str(self.timezone)})

    async def stop(self, *, wait: bool = False) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=wait)
        self._started = False
        logger.info("scheduler_stopped")

    def register_job(self, job: ScheduledJob) -> ScheduledJob:
        """Register one declarative job, replacing no existing registration."""
        self.registry.register(job)
        scheduling_options: dict[str, Any] = {}
        if not job.enabled:
            scheduling_options["next_run_time"] = None
        self.scheduler.add_job(
            self._execute_job,
            trigger=job.trigger,
            args=(job.id,),
            id=job.id,
            name=job.name,
            replace_existing=False,
            max_instances=job.max_instances,
            coalesce=job.coalesce,
            misfire_grace_time=job.misfire_grace_time,
            **scheduling_options,
        )
        logger.info("job_registered", extra={"job_id": job.id, "enabled": job.enabled})
        return job

    def pause_job(self, job_id: str) -> None:
        if self.registry.get(job_id) is None:
            raise KeyError(job_id)
        self.scheduler.pause_job(job_id)
        self.registry.disable(job_id)
        logger.info("job_paused", extra={"job_id": job_id})

    def resume_job(self, job_id: str) -> None:
        if self.registry.get(job_id) is None:
            raise KeyError(job_id)
        self.scheduler.resume_job(job_id)
        self.registry.enable(job_id)
        logger.info("job_resumed", extra={"job_id": job_id})

    def list_jobs(self) -> list[dict[str, Any]]:
        """Return scheduling state, next execution, and execution health."""
        result: list[dict[str, Any]] = []
        for definition in self.registry.list():
            scheduled = self.scheduler.get_job(definition.id)
            status = self.registry.status(definition.id)
            status.update(
                name=definition.name,
                next_run_time=scheduled.next_run_time if scheduled else None,
                paused=scheduled.next_run_time is None if scheduled else True,
            )
            result.append(status)
        return result

    def health_status(self) -> dict[str, Any]:
        """Expose scheduler, scheduled-job, and local async-queue health."""
        jobs = self.list_jobs()
        unhealthy = [item["job_id"] for item in jobs if item["status"] == "failed"]
        return {
            "scheduler": {"healthy": self.running, "running": self.running},
            "jobs": {"healthy": not unhealthy, "unhealthy_job_ids": unhealthy, "count": len(jobs)},
            # APScheduler's AsyncIO executor has no separate durable queue. External
            # queues can be checked by the injected health_check capability.
            "queue": {"healthy": self.running, "backend": "asyncio", "pending": None},
        }

    async def run_now(self, job_id: str) -> JobResult:
        """Run an existing job immediately without creating duplicate schedule logic."""
        if self.registry.get(job_id) is None:
            raise KeyError(job_id)
        return await self._execute_job(job_id)

    async def _execute_job(self, job_id: str) -> JobResult:
        job = self.registry.get(job_id)
        if job is None:
            raise KeyError(f"Unknown scheduled job: {job_id}")
        if not job.enabled:
            now = datetime.now(self.timezone)
            result = JobResult(job_id=job_id, status="skipped", started_at=now, finished_at=now)
            self.registry.record_result(job_id, result)
            return result

        for attempt in range(1, job.max_retries + 2):
            started_at = datetime.now(self.timezone)
            try:
                context: dict[str, Any] = {
                    "job_id": job.id,
                    "scheduled_at": started_at,
                    "attempt": attempt,
                    "metadata": job.metadata.copy(),
                }
                if job.id == "health_check":
                    context["scheduler_health"] = self.health_status()
                output = job.worker.run(
                    **context,
                )
                if inspect.isawaitable(output):
                    output = await output
                result = JobResult(
                    job_id=job.id,
                    status="success",
                    started_at=started_at,
                    finished_at=datetime.now(self.timezone),
                    attempt=attempt,
                    output=output,
                )
                self.registry.record_result(job.id, result)
                logger.info("job_succeeded", extra={"job_id": job.id, "attempt": attempt})
                return result
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                finished_at = datetime.now(self.timezone)
                retrying = attempt <= job.max_retries
                result = JobResult(
                    job_id=job.id,
                    status="retrying" if retrying else "failed",
                    started_at=started_at,
                    finished_at=finished_at,
                    attempt=attempt,
                    error=f"{type(exc).__name__}: {exc}",
                )
                self.registry.record_result(job.id, result)
                logger.exception("job_failed", extra={"job_id": job.id, "attempt": attempt, "retrying": retrying})
                if not retrying:
                    return result
                await asyncio.sleep(job.retry_delay_seconds * (2 ** (attempt - 1)))

        raise AssertionError("unreachable")


def build_default_scheduler_manager(
    *,
    capabilities: CapabilityRegistry,
    timezone_name: str = "UTC",
) -> SchedulerManager:
    """Create Atlas' standard capability-backed schedule without application coupling."""
    manager = SchedulerManager(timezone_name=timezone_name)
    jobs = (
        ScheduledJob("morning_brief", "Morning brief", MorningBriefWorker(capabilities), build_cron_trigger("0 7 * * 1-5", timezone_name)),
        ScheduledJob("watchlist_monitor", "Watchlist monitor", WatchlistMonitorWorker(capabilities), build_cron_trigger("*/15 9-16 * * 1-5", timezone_name)),
        ScheduledJob("market_monitor", "Market monitor", MarketMonitorWorker(capabilities), build_cron_trigger("*/5 9-16 * * 1-5", timezone_name)),
        ScheduledJob("earnings_monitor", "Earnings monitor", EarningsMonitorWorker(capabilities), build_interval_trigger(3600, timezone_name)),
        ScheduledJob("alert_dispatcher", "Alert dispatcher", AlertDispatcherWorker(capabilities), build_interval_trigger(60, timezone_name)),
        ScheduledJob("workspace_cleanup", "Workspace cleanup", WorkspaceCleanupWorker(capabilities), build_cron_trigger("0 3 * * *", timezone_name)),
        ScheduledJob("document_processor", "Document processor", DocumentProcessorWorker(capabilities), build_interval_trigger(300, timezone_name)),
        ScheduledJob("health_check", "Scheduler health check", HealthCheckWorker(capabilities), build_interval_trigger(60, timezone_name), max_retries=1),
    )
    for job in jobs:
        manager.register_job(job)
    return manager
