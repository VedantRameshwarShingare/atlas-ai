"""Company research tool with service-based dependency injection."""

from __future__ import annotations

from typing import Any, Protocol

from app.ai.enums import IntentType
from app.tools.base import BaseTool, ToolResult


class CompanyService(Protocol):
    """Service interface for company research data retrieval."""

    async def get_company_profile(self, symbol: str) -> dict[str, Any]:
        """Return structured company profile data."""

    async def get_company_news(self, symbol: str) -> list[dict[str, Any]]:
        """Return recent company news."""


class CompanyResearchTool(BaseTool):
    """Gather structured company research information without AI summarization."""

    name = "company_research"
    description = "Provides structured company overview and research context"
    supported_intents = (IntentType.COMPANY_RESEARCH,)

    def __init__(self, service: CompanyService) -> None:
        self._service = service

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the company research workflow."""
        symbol = kwargs.get("symbol", "")
        if not symbol:
            return ToolResult(success=False, tool_name=self.name, errors=["symbol is required"])

        profile = await self._service.get_company_profile(symbol)
        news = await self._service.get_company_news(symbol)

        data = {
            "symbol": symbol,
            "business_overview": profile.get("business_overview"),
            "industry": profile.get("industry"),
            "ceo": profile.get("ceo"),
            "market_cap": profile.get("market_cap"),
            "competitors": profile.get("competitors"),
            "financial_highlights": profile.get("financial_highlights"),
            "news": news,
            "investment_risks": profile.get("investment_risks"),
        }
        return ToolResult(success=True, tool_name=self.name, data=data, sources=[f"company:{symbol}"])
