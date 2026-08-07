"""Scheduler core helpers for Atlas AI."""

from __future__ import annotations

from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler


def create_scheduler(*, timezone_name: str = "UTC") -> AsyncIOScheduler:
    """Create an asyncio-based scheduler with timezone awareness."""
    return AsyncIOScheduler(timezone=ZoneInfo(timezone_name))
