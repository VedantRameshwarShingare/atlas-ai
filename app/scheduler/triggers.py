"""Trigger helpers for scheduler jobs."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger


def resolve_timezone(timezone_name: str | None) -> ZoneInfo | None:
    """Resolve a timezone name into a zoneinfo object."""
    if not timezone_name:
        return None
    return ZoneInfo(timezone_name)


def build_cron_trigger(expression: str, timezone_name: str | None = None) -> CronTrigger:
    """Create a cron trigger using the provided timezone."""
    return CronTrigger.from_crontab(expression, timezone=resolve_timezone(timezone_name))


def build_interval_trigger(seconds: int, timezone_name: str | None = None) -> IntervalTrigger:
    """Create an interval trigger using the provided timezone."""
    return IntervalTrigger(seconds=seconds, timezone=resolve_timezone(timezone_name))


def build_date_trigger(run_date: datetime | None = None, timezone_name: str | None = None) -> DateTrigger:
    """Create a one-off date trigger."""
    if run_date is not None and run_date.tzinfo is None:
        raise ValueError("run_date must be timezone-aware")
    return DateTrigger(run_date=run_date, timezone=resolve_timezone(timezone_name))
