"""Async/sync timing helpers for observability instrumentation."""

from __future__ import annotations

from contextlib import AbstractAsyncContextManager, AbstractContextManager
from time import perf_counter
from typing import Callable

from app.monitoring.metrics import Labels, MetricsRegistry, metrics


class PerformanceTimer(AbstractContextManager["PerformanceTimer"], AbstractAsyncContextManager["PerformanceTimer"]):
    """Measure an operation and publish the duration on completion."""

    def __init__(self, metric_name: str, *, registry: MetricsRegistry = metrics, labels: Labels | None = None, on_complete: Callable[[float], None] | None = None) -> None:
        self.metric_name, self.registry, self.labels, self.on_complete = metric_name, registry, labels, on_complete
        self.elapsed_seconds = 0.0
        self._started_at = 0.0

    def __enter__(self) -> "PerformanceTimer":
        self._started_at = perf_counter()
        return self

    def __exit__(self, *_: object) -> None:
        self.elapsed_seconds = perf_counter() - self._started_at
        self.registry.observe(self.metric_name, self.elapsed_seconds, labels=self.labels)
        if self.on_complete:
            self.on_complete(self.elapsed_seconds)

    async def __aenter__(self) -> "PerformanceTimer":
        return self.__enter__()

    async def __aexit__(self, *_: object) -> None:
        self.__exit__()
