"""Job registry for scheduler management."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from app.scheduler.jobs.base import ScheduledJob
from app.scheduler.jobs.job_result import JobResult


class JobRegistry:
    """Track registered jobs, enablement state, and execution history."""

    def __init__(self, *, history_limit: int = 100) -> None:
        if history_limit < 1:
            raise ValueError("history_limit must be positive")
        self._jobs: dict[str, ScheduledJob] = {}
        self._history: dict[str, list[JobResult]] = defaultdict(list)
        self._history_limit = history_limit

    def register(self, job: ScheduledJob) -> ScheduledJob:
        if job.id in self._jobs:
            raise ValueError(f"Job already registered: {job.id}")
        self._jobs[job.id] = job
        return job

    def enable(self, job_id: str) -> ScheduledJob | None:
        job = self._jobs.get(job_id)
        if job is not None:
            job.enabled = True
        return job

    def disable(self, job_id: str) -> ScheduledJob | None:
        job = self._jobs.get(job_id)
        if job is not None:
            job.enabled = False
        return job

    def get(self, job_id: str) -> ScheduledJob | None:
        return self._jobs.get(job_id)

    def list(self) -> list[ScheduledJob]:
        return list(self._jobs.values())

    def record_result(self, job_id: str, result: JobResult) -> None:
        history = self._history[job_id]
        history.append(result)
        del history[:-self._history_limit]

    def history(self, job_id: str) -> list[JobResult]:
        return list(self._history.get(job_id, []))

    def status(self, job_id: str) -> dict[str, Any]:
        job = self.get(job_id)
        if job is None:
            raise KeyError(job_id)
        history = self.history(job_id)
        last_result = history[-1] if history else None
        return {
            "job_id": job.id,
            "enabled": job.enabled,
            "status": last_result.status if last_result else "pending",
            "history_count": len(history),
            "last_result": last_result,
        }
