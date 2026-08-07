"""Market session and economic-event monitoring worker."""
from app.scheduler.workers.base import BaseWorker


class MarketMonitorWorker(BaseWorker):
    capability_name = "market_monitor"
