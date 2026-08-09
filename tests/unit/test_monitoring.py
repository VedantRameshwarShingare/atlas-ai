"""Unit coverage for framework-independent monitoring primitives."""

from __future__ import annotations

import pytest

from app.monitoring.health import HealthChecker
from app.monitoring.metrics import MetricsRegistry
from app.monitoring.performance import PerformanceTimer
from app.monitoring.tracing import capability_span, current_trace, end_trace, service_span, start_trace


@pytest.mark.asyncio
async def test_health_checker_runs_async_probes() -> None:
    checker = HealthChecker(
        {
            name: (lambda: True)
            for name in ("application", "database", "openai", "finnhub", "yahoo", "sec", "chromadb", "scheduler")
        }
    )
    report = await checker.check()
    assert report["healthy"] is True


def test_metrics_render_prometheus_text() -> None:
    registry = MetricsRegistry()
    with PerformanceTimer("atlas_test_latency", registry=registry, labels={"component": "test"}):
        pass
    registry.increment("atlas_test_total")
    assert "atlas_test_total" in registry.prometheus_text()


def test_trace_keeps_capability_and_service_chain() -> None:
    token = start_trace(request_id="request", correlation_id="correlation")
    try:
        with capability_span("brief"):
            with service_span("market_data"):
                assert current_trace().capability_chain == ("brief",)  # type: ignore[union-attr]
                assert current_trace().service_calls == ("market_data",)  # type: ignore[union-attr]
    finally:
        end_trace(token)
