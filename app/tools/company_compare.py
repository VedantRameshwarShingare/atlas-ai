"""Company comparison tool for structured financial benchmarking."""

from __future__ import annotations

from typing import Any, Protocol

from app.ai.enums import IntentType
from app.tools.base import BaseTool, ToolResult


class CompanyCompareService(Protocol):
    """Service interface for company comparison data."""

    async def compare_companies(self, symbols: list[str]) -> dict[str, Any]:
        """Return structured company comparison data."""


class CompanyCompareTool(BaseTool):
    """Compare financial metrics for multiple companies."""

    name = "company_compare"
    description = "Compares multiple companies across revenue, growth, valuation, and risks"
    supported_intents = (IntentType.COMPANY_RESEARCH,)

    def __init__(self, service: CompanyCompareService) -> None:
        self._service = service

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Compare a set of ticker symbols."""
        symbols = kwargs.get("symbols", [])
        if not symbols:
            return ToolResult(success=False, tool_name=self.name, errors=["symbols are required"])
        data = await self._service.compare_companies(symbols)
        return ToolResult(success=True, tool_name=self.name, data=data, sources=[f"compare:{','.join(symbols)}"])
