"""SEC filings tool for public company filing metadata."""

from __future__ import annotations

from typing import Any, Protocol

from app.ai.enums import IntentType
from app.tools.base import BaseTool, ToolResult


class SecFilingService(Protocol):
    """Service interface for SEC filing data retrieval."""

    async def get_filings(self, symbol: str) -> list[dict[str, Any]]:
        """Return filing metadata for a symbol."""


class SecFilingsTool(BaseTool):
    """Expose SEC filing metadata such as 10-K, 10-Q, and 8-K documents."""

    name = "sec_filings"
    description = "Provides SEC filing information and filing metadata"
    supported_intents = (IntentType.COMPANY_RESEARCH,)

    def __init__(self, service: SecFilingService) -> None:
        self._service = service

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Retrieve SEC filings for a symbol."""
        symbol = kwargs.get("symbol", "")
        if not symbol:
            return ToolResult(success=False, tool_name=self.name, errors=["symbol is required"])
        filings = await self._service.get_filings(symbol)
        return ToolResult(success=True, tool_name=self.name, data={"filings": filings}, sources=[f"sec:{symbol}"])
