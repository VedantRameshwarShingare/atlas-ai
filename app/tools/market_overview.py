"""Market overview tool for summary statistics and index data."""

from __future__ import annotations

from typing import Any, Protocol

from app.ai.enums import IntentType
from app.tools.base import BaseTool, ToolResult


class MarketOverviewService(Protocol):
    """Service interface for market overview data."""

    async def get_market_overview(self) -> dict[str, Any]:
        """Return structured market overview information."""


class MarketOverviewTool(BaseTool):
    """Provide major indexes, movers, sectors, and economic calendar context."""

    name = "market_overview"
    description = "Provides market snapshot and performance information"
    supported_intents = (IntentType.MARKET_NEWS, IntentType.MORNING_BRIEF)

    def __init__(self, service: MarketOverviewService) -> None:
        self._service = service

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Retrieve market overview data."""
        overview = await self._service.get_market_overview()
        return ToolResult(success=True, tool_name=self.name, data=overview, sources=["market:overview"])
