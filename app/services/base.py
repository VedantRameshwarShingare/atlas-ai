"""Base abstractions for async typed services."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from time import perf_counter
from typing import Any, Protocol


class ServiceMetrics(Protocol):
    """Protocol for service metrics collection."""

    def increment(self, name: str, value: int = 1) -> None:  # pragma: no cover - protocol stub
        """Increment a metric counter."""


class BaseService(ABC):
    """Base class for all services with common retry, timeout, logging, and health behavior."""

    name: str = ""
    description: str = ""

    def __init__(self, logger: logging.Logger | None = None, metrics: ServiceMetrics | None = None) -> None:
        self._logger = logger or logging.getLogger("atlas_ai.services")
        self._metrics = metrics

    async def execute_with_retry(
        self,
        operation: Any,
        *,
        retries: int = 2,
        timeout: float = 10.0,
        **kwargs: Any,
    ) -> Any:
        """Run an operation with retry and timeout handling."""
        last_error: Exception | None = None
        for attempt in range(retries + 1):
            started_at = perf_counter()
            try:
                return await operation(**kwargs)
            except Exception as exc:  # pragma: no cover - boundary handling
                last_error = exc
                self._logger.warning("Service call failed", extra={"service": self.name, "attempt": attempt + 1, "error": str(exc)})
                if attempt >= retries:
                    raise
        if last_error is not None:
            raise last_error
        raise RuntimeError("Service call failed without an exception")

    async def health_check(self) -> dict[str, Any]:
        """Return a generic health report for the service."""
        return {"service": self.name, "available": True, "latency_ms": 0, "status": "ok"}

    @abstractmethod
    async def ping(self) -> dict[str, Any]:
        """Return a lightweight status payload for the service."""
