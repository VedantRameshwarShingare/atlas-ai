"""Intent detection for routing user requests to the appropriate AI workflow."""

from __future__ import annotations

from app.ai.enums import IntentType, ToolType
from app.ai.types import IntentResult


class IntentDetector:
    """Detect the high-level intent of a user request."""

    def detect(self, text: str) -> IntentResult:
        """Return a structured intent classification and required tools."""
        lowered = text.lower()

        if "company" in lowered or "research" in lowered:
            return IntentResult(
                intent=IntentType.COMPANY_RESEARCH,
                confidence=0.85,
                required_tools=[ToolType.RESEARCH, ToolType.SEARCH],
            )

        if "news" in lowered or "market" in lowered:
            return IntentResult(
                intent=IntentType.MARKET_NEWS,
                confidence=0.8,
                required_tools=[ToolType.MARKET],
            )

        if "document" in lowered and ("summary" in lowered or "summarize" in lowered):
            return IntentResult(
                intent=IntentType.DOCUMENT_SUMMARY,
                confidence=0.9,
                required_tools=[ToolType.DOCUMENT],
            )

        if "document" in lowered and ("qa" in lowered or "question" in lowered):
            return IntentResult(
                intent=IntentType.DOCUMENT_QA,
                confidence=0.88,
                required_tools=[ToolType.DOCUMENT],
            )

        if "watchlist" in lowered or "portfolio" in lowered:
            return IntentResult(
                intent=IntentType.WATCHLIST,
                confidence=0.84,
                required_tools=[ToolType.WATCHLIST],
            )

        if "alert" in lowered:
            return IntentResult(
                intent=IntentType.ALERT,
                confidence=0.83,
                required_tools=[ToolType.ALERT],
            )

        if "meeting" in lowered or "prep" in lowered:
            return IntentResult(
                intent=IntentType.MEETING_PREP,
                confidence=0.82,
                required_tools=[ToolType.RESEARCH],
            )

        if "morning" in lowered or "brief" in lowered:
            return IntentResult(
                intent=IntentType.MORNING_BRIEF,
                confidence=0.8,
                required_tools=[ToolType.MARKET, ToolType.MEMORY],
            )

        if "search" in lowered:
            return IntentResult(
                intent=IntentType.SEARCH,
                confidence=0.76,
                required_tools=[ToolType.SEARCH],
            )

        if not text.strip():
            return IntentResult(intent=IntentType.UNKNOWN, confidence=0.0, required_tools=[])

        return IntentResult(intent=IntentType.CHAT, confidence=0.7, required_tools=[])
