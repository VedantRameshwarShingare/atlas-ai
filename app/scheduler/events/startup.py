"""Scheduler-specific startup hook for application composition roots."""

from __future__ import annotations

from app.scheduler.manager import SchedulerManager


async def startup_scheduler(manager: SchedulerManager) -> None:
    """Start a previously composed scheduler manager."""
    await manager.start()
