"""Watchlist tool backed by the workspace-scoped finance service."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from app.ai.enums import IntentType, ToolType
from app.services.finance.service import FinanceService
from app.tools.base import BaseTool, ToolResult


class WatchlistTool(BaseTool):
    """Manage workspace-scoped watchlist items."""

    name = "watchlist"
    description = "Adds, removes, and lists financial watchlist entries"
    tool_type = ToolType.WATCHLIST
    supported_intents = (IntentType.WATCHLIST,)

    def __init__(self, service: FinanceService) -> None:
        self._service = service

    async def execute(self, **kwargs: Any) -> ToolResult:
        request = kwargs.get("request")

        if request is None:
            raise ValueError("request is required")

        user_id = request.user_id
        if user_id is None:
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

        if (
            any(
                phrase in lowered
                for phrase in (
                    "remove ",
                    "delete ",
                    "take ",
                )
            )
            and "watchlist" in lowered
        ):
            if symbol is None:
                raise ValueError("No stock symbol found")

            await self._service.remove_watchlist_symbol(
                workspace_id=workspace_uuid,
                user_id=user_id,
                symbol=symbol,
            )

            return ToolResult(
                success=True,
                tool_name=self.name,
                tool_type=self.tool_type,
                data={
                    "action": "remove",
                    "symbol": symbol,
                },
            )

        if "add " in lowered and "watchlist" in lowered:
            if symbol is None:
                raise ValueError("No stock symbol found")

            item = await self._service.add_watchlist_symbol(
                workspace_id=workspace_uuid,
                user_id=user_id,
                symbol=symbol,
            )

            return ToolResult(
                success=True,
                tool_name=self.name,
                tool_type=self.tool_type,
                data={
                    "action": "add",
                    "symbol": item.symbol,
                    "company_name": item.company_name,
                },
            )

        items = await self._service.list_watchlist(
            workspace_id=workspace_uuid,
            user_id=user_id,
        )

        return ToolResult(
            success=True,
            tool_name=self.name,
            tool_type=self.tool_type,
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
        """Extract a ticker from common watchlist commands."""

        words = text.replace(",", " ").split()

        stopwords = {
            "ADD",
            "REMOVE",
            "DELETE",
            "TAKE",
            "FROM",
            "MY",
            "TO",
            "THE",
            "A",
            "WATCHLIST",
            "STOCK",
            "PLEASE",
        }

        for word in words:
            token = word.strip(".,!?():;").upper()

            if token in stopwords:
                continue

            if 1 <= len(token) <= 6 and token.replace(".", "").replace("-", "").isalnum():
                return token

        return None
