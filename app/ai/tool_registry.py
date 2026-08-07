"""Registry for AI tools and tool metadata."""

from __future__ import annotations

from typing import Any, Protocol

from app.ai.enums import ToolType


class Tool(Protocol):
    """Protocol describing the minimal tool interface."""

    name: str
    tool_type: ToolType

    async def execute(self, **kwargs: Any) -> Any:  # pragma: no cover - protocol stub
        """Execute the tool with the provided arguments."""


class ToolRegistry:
    """Register and resolve tools for the orchestration layer."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool by its name."""
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        """Return a registered tool by name."""
        return self._tools.get(name)

    def list(self) -> list[Tool]:
        """Return all registered tools."""
        return list(self._tools.values())

    def metadata(self, name: str) -> dict[str, Any] | None:
        """Return descriptive metadata for a registered tool."""
        tool = self.get(name)
        if tool is None:
            return None
        return {"name": tool.name, "tool_type": tool.tool_type.value}
