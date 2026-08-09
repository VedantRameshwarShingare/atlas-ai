"""Daily morning-brief worker."""

from app.scheduler.workers.base import BaseWorker


class MorningBriefWorker(BaseWorker):
    capability_name = "morning_brief"
