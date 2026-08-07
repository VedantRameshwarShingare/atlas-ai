"""Result models recorded for every background-job attempt."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

JobStatus = Literal["success", "failed", "retrying", "skipped"]


@dataclass(slots=True, frozen=True)
class JobResult:
    """Immutable execution record suitable for in-memory or durable history."""

    job_id: str
    status: JobStatus
    started_at: datetime
    finished_at: datetime
    attempt: int = 1
    output: Any = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def duration_seconds(self) -> float:
        return (self.finished_at - self.started_at).total_seconds()
