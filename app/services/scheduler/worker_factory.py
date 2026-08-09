from app.ai.capabilities import CapabilityRegistry
from app.scheduler.jobs.base import JobWorker
from app.scheduler.workers import (
    AlertDispatcherWorker,
    DocumentProcessorWorker,
    EarningsMonitorWorker,
    HealthCheckWorker,
    MarketMonitorWorker,
    MorningBriefWorker,
    WatchlistMonitorWorker,
    WorkspaceCleanupWorker,
)


def build_worker(
    job_type: str,
    capabilities: CapabilityRegistry,
) -> JobWorker:
    workers = {
        "document_processor": DocumentProcessorWorker,
        "market_monitor": MarketMonitorWorker,
        "watchlist_monitor": WatchlistMonitorWorker,
        "earnings_monitor": EarningsMonitorWorker,
        "alert_dispatcher": AlertDispatcherWorker,
        "morning_brief": MorningBriefWorker,
        "workspace_cleanup": WorkspaceCleanupWorker,
        "health_check": HealthCheckWorker,
    }

    worker_class = workers.get(job_type)

    if worker_class is None:
        raise ValueError(f"Unsupported scheduled job type: {job_type}")

    return worker_class(capabilities)