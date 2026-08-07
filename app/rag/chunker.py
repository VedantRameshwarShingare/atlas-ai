"""Chunking logic for RAG documents."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class Chunk:
    """A single text chunk with metadata."""

    id: str
    document_id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


class SemanticChunker:
    """Chunk documents into semantic segments with metadata."""

    async def chunk(self, *, document_id: str, text: str, metadata: dict[str, Any] | None = None) -> list[Chunk]:
        """Split text into chunks while preserving document metadata."""
        normalized_text = text.strip()
        if not normalized_text:
            return []
        parts = [part.strip() for part in normalized_text.split("\n\n") if part.strip()]
        chunks = []
        for index, part in enumerate(parts):
            chunks.append(
                Chunk(
                    id=f"{document_id}:chunk:{index}",
                    document_id=document_id,
                    text=part,
                    metadata={**(metadata or {}), "chunk_index": index},
                )
            )
        return chunks
