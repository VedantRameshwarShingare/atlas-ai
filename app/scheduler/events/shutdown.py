"""Scheduler-specific shutdown hook for application composition roots."""

from __future__ import annotations

from app.scheduler.manager import SchedulerManager


async def shutdown_scheduler(manager: SchedulerManager) -> None:
    """Stop the scheduler without waiting indefinitely for a worker."""
    await manager.stop(wait=False)
