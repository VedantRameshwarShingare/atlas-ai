"""Hugging Face embedding service."""

from __future__ import annotations

import asyncio
from typing import Any

from huggingface_hub import InferenceClient

from app.core.config import settings
from app.services.base import BaseService


class HuggingFaceEmbeddingsService(BaseService):
    """Generate embeddings using Hugging Face Inference Providers."""

    name = "huggingface_embeddings"
    description = "Generates text embeddings using Hugging Face"

    def __init__(self, client: InferenceClient | None = None) -> None:
        super().__init__()
        self._model = settings.huggingface.embedding_model

        self._client = client or InferenceClient(
            provider="hf-inference",
            token=(
                settings.huggingface.api_key.get_secret_value() if settings.huggingface.api_key is not None else None
            ),
        )

    async def create_embedding(
        self,
        *,
        input_text: str,
        model: str | None = None,
    ) -> list[float]:
        """Generate an embedding vector for text."""

        result = await asyncio.to_thread(
            self._client.feature_extraction,
            input_text,
            model=model or self._model,
        )

        return self._normalize_embedding(result)

    async def ping(self) -> dict[str, Any]:
        """Return service readiness metadata."""

        return {
            "service": self.name,
            "available": settings.huggingface.api_key is not None,
            "model": self._model,
        }

    @staticmethod
    def _normalize_embedding(result: Any) -> list[float]:
        """Normalize the provider response into a flat vector."""

        if hasattr(result, "tolist"):
            result = result.tolist()

        while isinstance(result, list) and result and isinstance(result[0], list):
            result = result[0]

        if not isinstance(result, list):
            raise TypeError("Embedding provider returned an invalid response")

        return [float(value) for value in result]
