"""Web search service abstraction."""

from __future__ import annotations

from typing import Any

from app.services.base import BaseService


class WebSearchService(BaseService):
    """Provide a unified web search interface for future providers."""

    name = "web_search"
    description = "Wraps external search providers"

    async def search(self, query: str) -> list[dict[str, Any]]:
        """Search for content matching the provided query."""
        return [{"query": query, "source": "web_search"}]

    async def ping(self) -> dict[str, Any]:
        """Return service readiness metadata."""
        return {"service": self.name, "available": True}
