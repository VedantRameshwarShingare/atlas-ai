"""OpenAI-compatible embeddings service abstraction."""

from __future__ import annotations

from typing import Any

from app.services.base import BaseService


class OpenAIEmbeddingsService(BaseService):
    """Wrap an embeddings-capable OpenAI-compatible client."""

    name = "openai_embeddings"
    description = "Handles embedding requests"

    def __init__(self, client: Any) -> None:
        super().__init__()
        self._client = client

    async def create_embedding(
        self,
        *,
        input_text: str,
        model: str | None = None,
    ) -> list[float]:
        """Create an embedding vector through the supplied client."""

        response = await self._client.embeddings.create(
            model=model or "text-embedding-3-small",
            input=input_text,
        )

        return list(response.data[0].embedding)

    async def ping(self) -> dict[str, Any]:
        """Return service readiness metadata."""

        return {
            "service": self.name,
            "available": True,
        }
