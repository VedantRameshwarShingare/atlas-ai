"""Watchlist event monitoring worker."""

from app.scheduler.workers.base import BaseWorker


class WatchlistMonitorWorker(BaseWorker):
    capability_name = "watchlist_monitor"
