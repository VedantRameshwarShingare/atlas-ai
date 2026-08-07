"""Context builder that merges memory, retrieved chunks, conversation, workspace, and capability results."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class RAGContext:
    """Context object returned by the RAG pipeline."""

    memory_context: str = ""
    retrieved_chunks: list[Any] = field(default_factory=list)
    conversation: list[Any] = field(default_factory=list)
    workspace: list[Any] = field(default_factory=list)
    capability_results: list[Any] = field(default_factory=list)
    citations: list[Any] = field(default_factory=list)


class ContextBuilder:
    """Merge memory, retrieval, conversation, and capability context into one object."""

    async def build(
        self,
        *,
        memory_context: str = "",
        retrieved_chunks: list[Any] | None = None,
        conversation: list[Any] | None = None,
        workspace: list[Any] | None = None,
        capability_results: list[Any] | None = None,
        citations: list[Any] | None = None,
    ) -> RAGContext:
        """Build a single context object from the supplied data."""
        return RAGContext(
            memory_context=memory_context,
            retrieved_chunks=retrieved_chunks or [],
            conversation=conversation or [],
            workspace=workspace or [],
            capability_results=capability_results or [],
            citations=citations or [],
        )
