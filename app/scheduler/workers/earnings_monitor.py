"""Upcoming, missed, and newly reported earnings worker."""

from app.scheduler.workers.base import BaseWorker


class EarningsMonitorWorker(BaseWorker):
    capability_name = "earnings_monitor"
