"""Capability abstractions for AI orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from app.ai.enums import ToolType


class Capability(Protocol):
    """Minimal interface for an AI capability."""

    name: str
    description: str

    async def execute(self, **kwargs: Any) -> Any:
        """Execute the capability with the provided arguments."""


class BaseCapability:
    """Base class for capabilities that depend on services."""

    name = ""
    description = ""
    tool_type = ToolType.UNKNOWN

    def __init__(self, *, services: dict[str, Any] | None = None) -> None:
        self.services = services or {}

    async def execute(self, **kwargs: Any) -> Any:
        raise NotImplementedError


@dataclass(slots=True)
class CapabilityExecutionResult:
    """Normalized output for an executed capability."""

    capability_name: str
    success: bool
    output: Any = None
    error: str | None = None


class CapabilityRegistry:
    """Register capabilities for orchestration."""

    def __init__(self) -> None:
        self._capabilities: dict[str, Capability] = {}

    def register(self, capability: Capability) -> None:
        self._capabilities[capability.name] = capability

    def get(self, name: str) -> Capability | None:
        return self._capabilities.get(name)

    def list(self) -> list[Capability]:
        return list(self._capabilities.values())


class CapabilityExecutor:
    """Execute registered capabilities and normalize their results."""

    def __init__(self, registry: CapabilityRegistry) -> None:
        self._registry = registry

    async def execute_many(
        self,
        capability_names: list[str],
        **kwargs: Any,
    ) -> list[CapabilityExecutionResult]:
        results: list[CapabilityExecutionResult] = []

        for name in capability_names:
            capability = self._registry.get(name)

            if capability is None:
                results.append(
                    CapabilityExecutionResult(
                        capability_name=name,
                        success=False,
                        error="Capability not found",
                    )
                )
                continue

            try:
                output = await capability.execute(**kwargs)
                results.append(
                    CapabilityExecutionResult(
                        capability_name=capability.name,
                        success=True,
                        output=output,
                    )
                )
            except Exception as exc:  # pragma: no cover - boundary handling
                results.append(
                    CapabilityExecutionResult(
                        capability_name=capability.name,
                        success=False,
                        error=str(exc),
                    )
                )

        return results
