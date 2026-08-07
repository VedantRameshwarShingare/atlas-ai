"""Earnings-related financial tool."""

from __future__ import annotations

from typing import Any, Protocol

from app.ai.enums import IntentType
from app.tools.base import BaseTool, ToolResult


class EarningsService(Protocol):
    """Service interface for earnings calendar and historical data."""

    async def get_earnings_calendar(self, symbol: str) -> list[dict[str, Any]]:
        """Return earnings calendar information."""

    async def get_earnings_history(self, symbol: str) -> list[dict[str, Any]]:
        """Return historical earnings data."""


class EarningsTool(BaseTool):
    """Provide upcoming and past earnings information with guidance."""

    name = "earnings"
    description = "Provides earnings calendar and historical earnings context"
    supported_intents = (IntentType.COMPANY_RESEARCH, IntentType.MORNING_BRIEF)

    def __init__(self, service: EarningsService) -> None:
        self._service = service

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Retrieve earnings data for a symbol."""
        symbol = kwargs.get("symbol", "")
        if not symbol:
            return ToolResult(success=False, tool_name=self.name, errors=["symbol is required"])
        calendar = await self._service.get_earnings_calendar(symbol)
        history = await self._service.get_earnings_history(symbol)
        return ToolResult(
            success=True,
            tool_name=self.name,
            data={"calendar": calendar, "history": history},
            sources=[f"earnings:{symbol}"],
        )
