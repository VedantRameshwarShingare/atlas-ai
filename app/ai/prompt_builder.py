"""Prompt assembly for AI orchestration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.ai.types import ConversationContext


class PromptBuilder:
    """Construct prompts by merging system templates with runtime context."""

    def __init__(self, prompts_dir: str | Path | None = None) -> None:
        self._prompts_dir = Path(prompts_dir or Path(__file__).resolve().parent / "prompts")

    def _read_template(self, filename: str) -> str:
        """Read a prompt template from disk."""
        template_path = self._prompts_dir / filename
        return template_path.read_text(encoding="utf-8") if template_path.exists() else ""

    def build(self, context: ConversationContext) -> str:
        """Merge system prompt, conversation, memory, tools, and request into one prompt."""
        system_prompt = self._read_template("system.md")
        routing_prompt = self._read_template("routing.md")

        sections: list[str] = []
        if system_prompt:
            sections.append(f"System:\n{system_prompt}")
        if routing_prompt:
            sections.append(f"Routing:\n{routing_prompt}")
        if context.conversation_history:
            sections.append(f"Conversation:\n{self._format_list(context.conversation_history)}")
        if context.memories:
            sections.append(f"Memory:\n{self._format_list(context.memories)}")
        if context.tool_results:
            sections.append(f"Tool Outputs:\n{self._format_list(context.tool_results)}")
        if context.workspace_context:
            sections.append(f"Workspace:\n{self._format_dict(context.workspace_context)}")
        if context.documents:
            sections.append(f"Documents:\n{self._format_list(context.documents)}")
        sections.append(f"Request:\n{context.request.text}")
        return "\n\n".join(sections)

    def _format_list(self, values: list[Any]) -> str:
        return "\n".join(str(value) for value in values)

    def _format_dict(self, values: dict[str, Any]) -> str:
        return "\n".join(f"{key}: {value}" for key, value in values.items())
