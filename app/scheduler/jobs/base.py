"""Base contracts for scheduled Atlas AI jobs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Protocol

from apscheduler.triggers.base import BaseTrigger

JobCallable = Callable[[], Awaitable[Any]]


class JobWorker(Protocol):
    """A worker invoked by a scheduled job."""

    async def run(self, **context: Any) -> Any:
        """Perform one unit of background work."""


@dataclass(slots=True)
class ScheduledJob:
    """Declarative scheduling definition; workers contain no trigger logic."""

    id: str
    name: str
    worker: JobWorker
    trigger: BaseTrigger
    enabled: bool = True
    max_retries: int = 3
    retry_delay_seconds: float = 5.0
    max_instances: int = 1
    coalesce: bool = True
    misfire_grace_time: int | None = 300
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("Scheduled job id is required")
        if self.max_retries < 0:
            raise ValueError("max_retries cannot be negative")
        if self.retry_delay_seconds < 0:
            raise ValueError("retry_delay_seconds cannot be negative")
        if self.max_instances < 1:
            raise ValueError("max_instances must be at least one")
