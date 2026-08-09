"""Reranking layer for retrieved RAG chunks."""

from __future__ import annotations

from typing import Any


class Reranker:
    """Rank retrieved chunks by relevance score."""

    async def rerank(
        self,
        *,
        chunks: list[Any],
        limit: int | None = None,
        similarity_threshold: float = 0.0,
    ) -> list[Any]:
        """Filter and rank chunks by similarity."""

        if limit is not None and limit <= 0:
            return []

        filtered_chunks = [chunk for chunk in chunks if self._similarity(chunk) >= similarity_threshold]

        ranked_chunks = sorted(
            filtered_chunks,
            key=self._similarity,
            reverse=True,
        )

        if limit is not None:
            return ranked_chunks[:limit]

        return ranked_chunks

    @staticmethod
    def _similarity(chunk: Any) -> float:
        """Extract a similarity score from a chunk."""

        if isinstance(chunk, dict):
            return float(chunk.get("similarity", 0.0))

        return float(getattr(chunk, "similarity", 0.0))
