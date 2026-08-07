"""OpenAI client configuration abstraction."""

from __future__ import annotations

from typing import Any

from app.services.base import BaseService


class OpenAIClientService(BaseService):
    """Central configuration wrapper for OpenAI client access."""

    name = "openai_client"
    description = "Configures and exposes OpenAI client behavior"

    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        super().__init__()
        self._api_key = api_key
        self._model = model

    async def ping(self) -> dict[str, Any]:
        """Return client readiness metadata."""
        return {"service": self.name, "available": bool(self._api_key), "model": self._model}
