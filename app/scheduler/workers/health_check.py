"""Scheduler and queue health-check worker."""

from app.scheduler.workers.base import BaseWorker


class HealthCheckWorker(BaseWorker):
    capability_name = "health_check"
