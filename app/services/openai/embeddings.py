"""OpenAI embeddings service abstraction."""

from __future__ import annotations

from typing import Any

from app.services.base import BaseService


class OpenAIEmbeddingsService(BaseService):
    """Wrap OpenAI embeddings operations without business logic."""

    name = "openai_embeddings"
    description = "Handles OpenAI embedding requests"

    def __init__(self, client: Any) -> None:
        super().__init__()
        self._client = client

    async def create_embedding(self, *, input_text: str, model: str | None = None) -> dict[str, Any]:
        """Create an embedding payload through the supplied client."""
        return {"model": model or "text-embedding-3-small", "input": input_text}

    async def ping(self) -> dict[str, Any]:
        """Return service readiness metadata."""
        return {"service": self.name, "available": True}
