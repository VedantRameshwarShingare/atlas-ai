"""Retrieval layer for the RAG pipeline."""

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
    """Filter, rank, and limit vector-search results."""

    async def retrieve(
        self,
        *,
        query: str,
        chunks: list[dict[str, Any]],
        limit: int = 5,
        similarity_threshold: float = 0.0,
        document_id: str | None = None,
    ) -> list[RetrievedChunk]:
        """Return the most relevant chunks matching the retrieval criteria."""

        if limit <= 0:
            return []

        filtered_chunks: list[dict[str, Any]] = []

        for chunk in chunks:
            similarity = float(chunk.get("similarity", 0.0))

            if similarity < similarity_threshold:
                continue

            if document_id is not None:
                chunk_document_id = str(chunk.get("document_id", ""))

                if chunk_document_id != document_id:
                    continue

            filtered_chunks.append(chunk)

        filtered_chunks.sort(
            key=lambda chunk: (
                -float(chunk.get("similarity", 0.0)),
                str(chunk.get("id", chunk.get("chunk_id", ""))),
            )
        )

        results: list[RetrievedChunk] = []

        for chunk in filtered_chunks[:limit]:
            results.append(
                RetrievedChunk(
                    chunk_id=str(chunk.get("chunk_id", chunk.get("id", ""))),
                    document_id=str(chunk.get("document_id", "")),
                    text=str(chunk.get("text", "")),
                    metadata=chunk.get("metadata", {}),
                    similarity=float(chunk.get("similarity", 0.0)),
                )
            )

        return results
