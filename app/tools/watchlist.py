"""Watchlist tool backed by the workspace-scoped finance service."""

from __future__ import annotations

import re
from typing import Any
from uuid import UUID

from app.ai.enums import IntentType, ToolType
from app.ai.types import ChatRequest
from app.services.finance.service import FinanceService
from app.tools.base import BaseTool, ToolResult

_SYMBOL_PATTERN = re.compile(r"\b[A-Z]{1,6}(?:\.[A-Z])?\b")

_COMPANY_SYMBOLS = {
    "apple": "AAPL",
    "microsoft": "MSFT",
    "google": "GOOGL",
    "alphabet": "GOOGL",
    "amazon": "AMZN",
    "tesla": "TSLA",
    "nvidia": "NVDA",
    "meta": "META",
}


class WatchlistTool(BaseTool):
    """Manage workspace-scoped watchlist entries."""

    name = "watchlist"
    description = "Adds, removes, and lists financial watchlist entries"
    tool_type = ToolType.WATCHLIST
    supported_intents = (IntentType.WATCHLIST,)

    def __init__(self, service: FinanceService) -> None:
        self._service = service

    async def execute(self, **kwargs: Any) -> ToolResult:
        request = kwargs.get("request")

        if not isinstance(request, ChatRequest):
            raise ValueError("request must be a ChatRequest")

        if request.user_id is None:
            raise ValueError("Authenticated user is required")

        workspace_id = request.metadata.get("workspace_id")

        if not workspace_id:
            raise ValueError("Workspace context is required")

        try:
            workspace_uuid = UUID(str(workspace_id))
        except ValueError as exc:
            raise ValueError("Invalid workspace_id") from exc

        text = request.text.strip()
        lowered = text.lower()

        symbol = self._extract_symbol(text)

        # ADD
        if "add" in lowered and "watchlist" in lowered:
            if symbol is None:
                raise ValueError("No stock symbol found")

            item = await self._service.add_watchlist_symbol(
                workspace_id=workspace_uuid,
                user_id=request.user_id,
                symbol=symbol,
            )

            return ToolResult(
                success=True,
                tool_name=self.name,
                data={
                    "action": "add",
                    "symbol": item.symbol,
                    "company_name": item.company_name,
                },
            )

        # REMOVE
        if ("remove" in lowered or "delete" in lowered) and "watchlist" in lowered:
            if symbol is None:
                raise ValueError("No stock symbol found")

            await self._service.remove_watchlist_symbol(
                workspace_id=workspace_uuid,
                user_id=request.user_id,
                symbol=symbol,
            )

            return ToolResult(
                success=True,
                tool_name=self.name,
                data={
                    "action": "remove",
                    "symbol": symbol,
                },
            )

        # LIST
        items = await self._service.list_watchlist(
            workspace_id=workspace_uuid,
            user_id=request.user_id,
        )

        return ToolResult(
            success=True,
            tool_name=self.name,
            data={
                "action": "list",
                "items": [
                    {
                        "symbol": item.symbol,
                        "company_name": item.company_name,
                        "market": item.market,
                        "is_active": item.is_active,
                    }
                    for item in items
                ],
            },
        )

    @staticmethod
    def _extract_symbol(text: str) -> str | None:
        """Extract a ticker or common company name from user text."""

        lowered = text.lower()

        for company, symbol in _COMPANY_SYMBOLS.items():
            if re.search(rf"\b{re.escape(company)}\b", lowered):
                return symbol

        stopwords = {
            "ADD",
            "REMOVE",
            "DELETE",
            "MY",
            "TO",
            "FROM",
            "THE",
            "A",
            "AN",
            "AND",
            "WATCHLIST",
            "STOCK",
            "PRICE",
            "PLEASE",
        }

        for token in _SYMBOL_PATTERN.findall(text.upper()):
            if token not in stopwords:
                return token

        return None
