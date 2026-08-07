"""Unified search tool interface for future source integrations."""

from __future__ import annotations

from typing import Any

from app.ai.enums import IntentType
from app.tools.base import BaseTool, ToolResult


class SearchTool(BaseTool):
    """Unified search interface for news, companies, documents, memory, and workspace content."""

    name = "search"
    description = "Searches across future support sources"
    supported_intents = (IntentType.SEARCH, IntentType.COMPANY_RESEARCH)

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Return a standardized placeholder result for future search integrations."""
        query = kwargs.get("query", "")
        return ToolResult(success=True, tool_name=self.name, data={"query": query, "results": []}, warnings=["Search integrations are not implemented yet"])
