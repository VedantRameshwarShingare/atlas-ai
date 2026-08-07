"""Health check tool for provider and service availability."""

from __future__ import annotations

from typing import Any, Protocol

from app.tools.base import BaseTool, ToolResult


class HealthService(Protocol):
    """Service interface for provider health checks."""

    async def get_health_status(self) -> dict[str, Any]:
        """Return health status information for a provider."""


class HealthTool(BaseTool):
    """Return availability and status information for external providers."""

    name = "health"
    description = "Reports provider availability, latency, and service status"
    supported_intents = ()

    def __init__(self, service: HealthService) -> None:
        self._service = service

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Retrieve health status from the configured provider service."""
        status = await self._service.get_health_status()
        return ToolResult(success=True, tool_name=self.name, data=status, sources=["health:status"])
