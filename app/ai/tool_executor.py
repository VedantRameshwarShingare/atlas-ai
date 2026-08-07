"""Tool execution layer for orchestrated AI workflows."""

from __future__ import annotations

from typing import Any

from app.ai.enums import ToolType
from app.ai.tool_registry import ToolRegistry
from app.ai.types import ToolResult


class ToolExecutor:
    """Execute registered tools and normalize their results."""

    def __init__(self, registry: ToolRegistry) -> None:
        self._registry = registry

    async def execute_many(self, tool_names: list[str], **kwargs: Any) -> list[ToolResult]:
        """Execute a list of tools and return standardized results."""
        results: list[ToolResult] = []
        for name in tool_names:
            tool = self._registry.get(name)
            if tool is None:
                results.append(
                    ToolResult(
                        tool_name=name,
                        tool_type=ToolType.UNKNOWN,
                        success=False,
                        error="Tool not found",
                    )
                )
                continue

            try:
                output = await tool.execute(**kwargs)
                results.append(
                    ToolResult(
                        tool_name=tool.name,
                        tool_type=tool.tool_type,
                        success=True,
                        output=output,
                    )
                )
            except Exception as exc:  # pragma: no cover - boundary handling
                results.append(
                    ToolResult(
                        tool_name=tool.name,
                        tool_type=tool.tool_type,
                        success=False,
                        error=str(exc),
                    )
                )

        return results
