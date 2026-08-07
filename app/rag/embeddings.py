"""Embedding abstraction for RAG using services."""

from __future__ import annotations

from typing import Any

from app.services.openai.embeddings import OpenAIEmbeddingsService


class EmbeddingEngine:
    """Generate and manage embeddings without calling OpenAI directly."""

    def __init__(self, *, service: OpenAIEmbeddingsService | None = None) -> None:
        self._service = service

    async def embed_text(self, *, text: str, model: str | None = None) -> dict[str, Any]:
        """Create an embedding payload via the service abstraction."""
        if self._service is None:
            return {"model": model or "text-embedding-3-small", "input": text, "embedded": False}
        return await self._service.create_embedding(input_text=text, model=model)
