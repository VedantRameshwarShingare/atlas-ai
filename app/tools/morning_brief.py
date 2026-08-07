"""Morning brief tool for daily research highlights."""

from __future__ import annotations

from typing import Any, Protocol

from app.ai.enums import IntentType
from app.tools.base import BaseTool, ToolResult


class MorningBriefService(Protocol):
    """Service interface for morning brief data."""

    async def get_morning_brief(self) -> dict[str, Any]:
        """Return structured morning brief data."""


class MorningBriefTool(BaseTool):
    """Assemble a structured morning brief with market and watchlist context."""

    name = "morning_brief"
    description = "Provides market overview, watchlist updates, and action items"
    supported_intents = (IntentType.MORNING_BRIEF,)

    def __init__(self, service: MorningBriefService) -> None:
        self._service = service

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Retrieve the morning brief payload."""
        data = await self._service.get_morning_brief()
        return ToolResult(success=True, tool_name=self.name, data=data, sources=["morning:brief"])
