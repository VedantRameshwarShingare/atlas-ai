"""Expired workspace and temporary-context cleanup worker."""
from app.scheduler.workers.base import BaseWorker


class WorkspaceCleanupWorker(BaseWorker):
    capability_name = "workspace_cleanup"
