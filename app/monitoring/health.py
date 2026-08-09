"""Composable async health checks for Atlas dependencies."""

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from dataclasses import asdict, dataclass
from typing import Any

HealthProbe = Callable[[], Awaitable[Any] | Any]
REQUIRED_COMPONENTS = ("application", "database", "openai", "finnhub", "yahoo", "sec", "chromadb", "scheduler")


@dataclass(slots=True, frozen=True)
class ComponentHealth:
    name: str
    healthy: bool
    detail: str | None = None


class HealthChecker:
    """Runs injected dependency probes without owning any application service."""

    def __init__(self, probes: dict[str, HealthProbe] | None = None) -> None:
        self._probes = probes or {}

    def register(self, name: str, probe: HealthProbe) -> None:
        self._probes[name] = probe

    async def check(self) -> dict[str, Any]:
        components: list[ComponentHealth] = []
        for name in REQUIRED_COMPONENTS:
            probe = self._probes.get(name)
            if probe is None:
                components.append(ComponentHealth(name, False, "probe not configured"))
                continue
            try:
                result = probe()
                if inspect.isawaitable(result):
                    result = await result
                healthy = result is not False
                components.append(ComponentHealth(name, healthy, None if healthy else "probe reported unhealthy"))
            except Exception as exc:
                components.append(ComponentHealth(name, False, f"{type(exc).__name__}: {exc}"))
        return {
            "healthy": all(component.healthy for component in components),
            "components": [asdict(component) for component in components],
        }
