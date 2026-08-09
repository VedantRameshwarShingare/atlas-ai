"""Small, dependency-free metrics registry with Prometheus exposition support."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass, field
from threading import Lock
from time import perf_counter

Labels = Mapping[str, str | int | float | bool]


def _labels_key(labels: Labels | None) -> tuple[tuple[str, str], ...]:
    return tuple(sorted((key, str(value)) for key, value in (labels or {}).items()))


def _render_labels(labels: tuple[tuple[str, str], ...]) -> str:
    if not labels:
        return ""
    escaped = (f'{key}="{value.replace(chr(34), chr(92) + chr(34))}"' for key, value in labels)
    return "{" + ",".join(escaped) + "}"


@dataclass(slots=True)
class MetricsRegistry:
    """In-process metrics, designed for later replacement by a Prometheus client."""

    _counters: dict[str, dict[tuple[tuple[str, str], ...], float]] = field(default_factory=lambda: defaultdict(dict))
    _durations: dict[str, dict[tuple[tuple[str, str], ...], list[float]]] = field(
        default_factory=lambda: defaultdict(dict)
    )
    _lock: Lock = field(default_factory=Lock)

    def increment(self, name: str, value: float = 1, *, labels: Labels | None = None) -> None:
        key = _labels_key(labels)
        with self._lock:
            self._counters[name][key] = self._counters[name].get(key, 0.0) + value

    def observe(self, name: str, seconds: float, *, labels: Labels | None = None) -> None:
        key = _labels_key(labels)
        with self._lock:
            self._durations[name].setdefault(key, []).append(seconds)

    def timer(self, name: str, *, labels: Labels | None = None) -> MetricTimer:
        return MetricTimer(self, name, labels)

    def prometheus_text(self) -> str:
        """Render counters and latency summaries in Prometheus text format."""
        lines: list[str] = []
        with self._lock:
            for name, series in self._counters.items():
                lines.append(f"# TYPE {name} counter")
                lines.extend(f"{name}{_render_labels(labels)} {value}" for labels, value in series.items())
            for name, series in self._durations.items():
                lines.append(f"# TYPE {name}_seconds summary")
                for labels, values in series.items():
                    total = sum(values)
                    lines.append(f"{name}_seconds_count{_render_labels(labels)} {len(values)}")
                    lines.append(f"{name}_seconds_sum{_render_labels(labels)} {total}")
        return "\n".join(lines) + ("\n" if lines else "")


class MetricTimer:
    """Context manager that records elapsed seconds when the scope exits."""

    def __init__(self, registry: MetricsRegistry, name: str, labels: Labels | None) -> None:
        self._registry, self._name, self._labels = registry, name, labels
        self._started_at = 0.0

    def __enter__(self) -> MetricTimer:
        self._started_at = perf_counter()
        return self

    def __exit__(self, *_: object) -> None:
        self._registry.observe(self._name, perf_counter() - self._started_at, labels=self._labels)


metrics = MetricsRegistry()

# Canonical metric names used by request logging, capabilities, services, and jobs.
REQUEST_COUNT = "atlas_requests_total"
RESPONSE_TIME = "atlas_response_time"
CAPABILITY_EXECUTION_TIME = "atlas_capability_execution_time"
SERVICE_LATENCY = "atlas_service_latency"
SCHEDULER_JOB_COUNT = "atlas_scheduler_jobs_total"
SCHEDULER_JOB_TIME = "atlas_scheduler_job_time"
MEMORY_RETRIEVAL_TIME = "atlas_memory_retrieval_time"
RAG_RETRIEVAL_TIME = "atlas_rag_retrieval_time"
