"""Optional ASGI middleware for correlated request logs and metrics."""

from __future__ import annotations

import logging
from time import perf_counter

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.monitoring.metrics import REQUEST_COUNT, RESPONSE_TIME, MetricsRegistry, metrics
from app.monitoring.tracing import current_trace, end_trace, start_trace


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log one structured event per request and propagate correlation headers."""

    def __init__(
        self, app: object, *, registry: MetricsRegistry = metrics, logger: logging.Logger | None = None
    ) -> None:
        super().__init__(app)  # type: ignore[arg-type]
        self.registry = registry
        self.logger = logger or logging.getLogger("atlas_ai.requests")

    async def dispatch(self, request: Request, call_next: object) -> Response:
        request_id = request.headers.get("X-Request-ID")
        correlation_id = request.headers.get("X-Correlation-ID")
        token = start_trace(request_id=request_id, correlation_id=correlation_id)
        started_at = perf_counter()
        status_code = 500
        try:
            response = await call_next(request)  # type: ignore[operator]
            status_code = response.status_code
            trace = current_trace()
            if trace:
                response.headers["X-Request-ID"] = trace.request_id
                response.headers["X-Correlation-ID"] = trace.correlation_id
            return response
        finally:
            elapsed = perf_counter() - started_at
            labels = {"method": request.method, "path": request.url.path, "status_code": status_code}
            self.registry.increment(REQUEST_COUNT, labels=labels)
            self.registry.observe(RESPONSE_TIME, elapsed, labels=labels)
            trace = current_trace()
            self.logger.info(
                "request_completed",
                extra={
                    "request_id": trace.request_id if trace else None,
                    "correlation_id": trace.correlation_id if trace else None,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": status_code,
                    "duration_seconds": elapsed,
                },
            )
            end_trace(token)
