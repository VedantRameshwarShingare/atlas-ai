"""Base abstractions for financial tools."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from time import perf_counter
from typing import Any, Protocol

from app.ai.enums import IntentType


@dataclass(slots=True)
class ToolResult:
    """Standardized result object returned by every financial tool."""

    success: bool
    tool_name: str
    execution_time: float = 0.0
    data: dict[str, Any] | None = None
    sources: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class Service(Protocol):
    """Protocol describing a service dependency for a tool."""


class BaseTool(ABC):
    """Abstract base class for all financial tools."""

    name: str = ""
    description: str = ""
    supported_intents: tuple[IntentType, ...] = ()

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the tool with the provided input."""

    def validate(self, **kwargs: Any) -> None:
        """Validate the supplied arguments before execution."""
        return None

    def format_output(self, data: Any) -> dict[str, Any]:
        """Normalize tool-specific output into a serializable dictionary."""
        return {"value": data}

    async def health_check(self) -> ToolResult:
        """Return basic health status for the tool."""
        return ToolResult(
            success=True,
            tool_name=self.name,
            data={"status": "ok"},
            metadata={"component": self.__class__.__name__},
        )

    async def _execute_with_timing(self, handler: Any, **kwargs: Any) -> ToolResult:
        """Wrap execution with timing and error capture."""
        started_at = perf_counter()
        try:
            self.validate(**kwargs)
            result = await handler(**kwargs)
            execution_time = perf_counter() - started_at
            return ToolResult(
                success=True,
                tool_name=self.name,
                execution_time=execution_time,
                data=result,
            )
        except Exception as exc:  # pragma: no cover - boundary handling
            execution_time = perf_counter() - started_at
            return ToolResult(
                success=False,
                tool_name=self.name,
                execution_time=execution_time,
                errors=[str(exc)],
            )
