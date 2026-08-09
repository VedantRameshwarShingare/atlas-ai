"""Embedding abstraction for RAG."""

from __future__ import annotations

from app.services.huggingface.embeddings import HuggingFaceEmbeddingsService


class EmbeddingEngine:
    """Generate embeddings through the configured embedding service."""

    def __init__(
        self,
        *,
        service: HuggingFaceEmbeddingsService | None = None,
    ) -> None:
        self._service = service or HuggingFaceEmbeddingsService()

    async def embed_text(
        self,
        *,
        text: str,
        model: str | None = None,
    ) -> list[float]:
        """Create an embedding vector."""

        return await self._service.create_embedding(
            input_text=text,
            model=model,
        )
