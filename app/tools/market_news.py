"""Market news tool for structured article retrieval."""

from __future__ import annotations

from typing import Any, Protocol

from app.ai.enums import IntentType
from app.tools.base import BaseTool, ToolResult


class MarketNewsService(Protocol):
    """Service interface for market news retrieval."""

    async def get_latest_news(self, category: str | None = None) -> list[dict[str, Any]]:
        """Return structured market news articles."""


class MarketNewsTool(BaseTool):
    """Return latest market headlines and events in structured form."""

    name = "market_news"
    description = "Provides latest market news, headlines, and events"
    supported_intents = (IntentType.MARKET_NEWS,)

    def __init__(self, service: MarketNewsService) -> None:
        self._service = service

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute news retrieval."""
        category = kwargs.get("category")
        articles = await self._service.get_latest_news(category=category)
        return ToolResult(success=True, tool_name=self.name, data={"articles": articles}, sources=["market:news"])
