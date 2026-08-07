"""Scheduler interface for recurring background tasks."""

from __future__ import annotations

from typing import Any

from app.services.base import BaseService


class SchedulerService(BaseService):
    """Provide scheduling hooks for recurring tasks such as morning brief and scans."""

    name = "scheduler"
    description = "Wraps recurring task scheduling"

    async def schedule(self, *, task_name: str, cron_expression: str) -> dict[str, Any]:
        """Register a scheduled task."""
        return {"task_name": task_name, "cron_expression": cron_expression}

    async def run_now(self, *, task_name: str) -> dict[str, Any]:
        """Run a scheduled task immediately."""
        return {"task_name": task_name}

    async def ping(self) -> dict[str, Any]:
        """Return service readiness metadata."""
        return {"service": self.name, "available": True}
