"""Document analysis tool interface for future document-processing integrations."""

from __future__ import annotations

from typing import Any

from app.ai.enums import IntentType
from app.tools.base import BaseTool, ToolResult


class DocumentAnalysisTool(BaseTool):
    """Interface-only document analysis tool for summarization and QA workflows."""

    name = "document_analysis"
    description = "Provides document summarization, extraction, and QA interfaces"
    supported_intents = (IntentType.DOCUMENT_SUMMARY, IntentType.DOCUMENT_QA)

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Return a placeholder result indicating the tool is not implemented."""
        return ToolResult(
            success=True,
            tool_name=self.name,
            data={"status": "interface_only"},
            warnings=["No document processing implementation yet"],
        )

    async def summarize(self, **kwargs: Any) -> ToolResult:
        """Placeholder for document summarization."""
        return ToolResult(success=True, tool_name=self.name, data={"action": "summarize"})

    async def extract(self, **kwargs: Any) -> ToolResult:
        """Placeholder for document extraction."""
        return ToolResult(success=True, tool_name=self.name, data={"action": "extract"})

    async def compare(self, **kwargs: Any) -> ToolResult:
        """Placeholder for document comparison."""
        return ToolResult(success=True, tool_name=self.name, data={"action": "compare"})

    async def question_answer(self, **kwargs: Any) -> ToolResult:
        """Placeholder for document question-answering."""
        return ToolResult(success=True, tool_name=self.name, data={"action": "question_answer"})
