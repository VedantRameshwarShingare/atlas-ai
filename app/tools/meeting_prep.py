"""Meeting preparation tool for research summary generation."""

from __future__ import annotations

from typing import Any, Protocol

from app.ai.enums import IntentType
from app.tools.base import BaseTool, ToolResult


class MeetingPrepService(Protocol):
    """Service interface for meeting preparation data."""

    async def get_meeting_brief(self, company: str) -> dict[str, Any]:
        """Return structured meeting preparation context."""


class MeetingPrepTool(BaseTool):
    """Provide meeting brief, agenda, and company context."""

    name = "meeting_prep"
    description = "Provides meeting brief, agenda, company context, and talking points"
    supported_intents = (IntentType.MEETING_PREP,)

    def __init__(self, service: MeetingPrepService) -> None:
        self._service = service

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Create a structured meeting preparation payload."""
        company = kwargs.get("company", "")
        if not company:
            return ToolResult(success=False, tool_name=self.name, errors=["company is required"])
        data = await self._service.get_meeting_brief(company)
        return ToolResult(success=True, tool_name=self.name, data=data, sources=[f"meeting:{company}"])
