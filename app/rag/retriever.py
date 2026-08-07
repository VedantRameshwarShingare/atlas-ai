"""Hybrid retrieval interface for RAG."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class RetrievedChunk:
    """A retrieved chunk with relevance metadata."""

    chunk_id: str
    document_id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    similarity: float = 0.0


class Retriever:
    """Abstract retrieval interface for future hybrid implementations."""

    async def retrieve(self, *, query: str, chunks: list[dict[str, Any]], limit: int = 5) -> list[RetrievedChunk]:
        """Return relevant chunks with metadata and similarity values."""
        results = []
        for chunk in chunks[:limit]:
            results.append(
                RetrievedChunk(
                    chunk_id=str(chunk.get("chunk_id", "")),
                    document_id=str(chunk.get("document_id", "")),
                    text=str(chunk.get("text", "")),
                    metadata=chunk.get("metadata", {}),
                    similarity=float(chunk.get("similarity", 0.0)),
                )
            )
        return results
