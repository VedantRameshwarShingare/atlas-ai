"""Watchlist tool for managing symbolic watchlists."""

from __future__ import annotations

from typing import Any, Protocol

from app.ai.enums import IntentType
from app.tools.base import BaseTool, ToolResult


class WatchlistService(Protocol):
    """Service interface for watchlist operations."""

    async def add_symbol(self, user_id: str, symbol: str) -> dict[str, Any]:
        """Add a symbol to a watchlist."""

    async def remove_symbol(self, user_id: str, symbol: str) -> dict[str, Any]:
        """Remove a symbol from a watchlist."""

    async def list_symbols(self, user_id: str) -> list[dict[str, Any]]:
        """List watchlist entries."""

    async def update_symbol(self, user_id: str, symbol: str, **kwargs: Any) -> dict[str, Any]:
        """Update watchlist entry metadata."""


class WatchlistTool(BaseTool):
    """Manage watchlist items for a user."""

    name = "watchlist"
    description = "Manages watchlist entries and monitoring state"
    supported_intents = (IntentType.WATCHLIST,)

    def __init__(self, service: WatchlistService) -> None:
        self._service = service

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Dispatch watchlist actions based on the requested operation."""
        action = kwargs.get("action", "list")
        user_id = kwargs.get("user_id", "")
        symbol = kwargs.get("symbol", "")

        if action == "add":
            data = await self._service.add_symbol(user_id, symbol)
        elif action == "remove":
            data = await self._service.remove_symbol(user_id, symbol)
        elif action == "update":
            data = await self._service.update_symbol(user_id, symbol, **kwargs)
        else:
            data = await self._service.list_symbols(user_id)

        return ToolResult(success=True, tool_name=self.name, data={"action": action, "result": data})
