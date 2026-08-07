"""Notification dispatch worker; delivery implementation belongs to capabilities/services."""
from app.scheduler.workers.base import BaseWorker


class AlertDispatcherWorker(BaseWorker):
    capability_name = "alert_dispatcher"
