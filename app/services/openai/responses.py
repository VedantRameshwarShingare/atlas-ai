"""OpenAI Responses API service abstraction."""

from __future__ import annotations

from typing import Any

from app.services.base import BaseService


class OpenAIResponsesService(BaseService):
    """Wrap OpenAI Responses API interactions without business logic."""

    name = "openai_responses"
    description = "Handles OpenAI Responses API requests"

    def __init__(self, client: Any) -> None:
        super().__init__()
        self._client = client

    async def create_response(
        self, *, input_text: str, model: str | None = None, temperature: float = 0.2
    ) -> dict[str, Any]:
        """Create a response payload through the supplied client."""
        return {"model": model or "gpt-4o-mini", "input": input_text, "temperature": temperature}

    async def ping(self) -> dict[str, Any]:
        """Return service readiness metadata."""
        return {"service": self.name, "available": True}
