"""Placeholder reranker abstraction for future ranking strategies."""

from __future__ import annotations

from typing import Any


class Reranker:
    """Interface-only reranker for future ranking pipeline integration."""

    async def rerank(self, *, chunks: list[Any]) -> list[Any]:
        """Return the incoming chunks without modification."""
        return chunks
