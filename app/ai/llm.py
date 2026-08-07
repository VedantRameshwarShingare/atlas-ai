"""Async OpenAI Responses API wrapper."""

from __future__ import annotations

import asyncio
from typing import Any, Protocol

from app.config import settings


class SupportsResponsesAPI(Protocol):
    """Protocol describing the minimal OpenAI client surface used by the wrapper."""

    async def responses_create(self, **kwargs: Any) -> Any:  # pragma: no cover - protocol stub
        """Create a response through the OpenAI Responses API."""


class OpenAIClient:
    """Central wrapper for all OpenAI API calls."""

    def __init__(self, client: SupportsResponsesAPI | None = None) -> None:
        self._client = client
        self._model = settings.openai_model
        self._api_key = settings.openai_api_key

    async def create_response(
        self,
        *,
        model: str | None = None,
        input_text: str | None = None,
        temperature: float = 0.2,
        timeout: float = 30.0,
        max_retries: int = 2,
        **kwargs: Any,
    ) -> Any:
        """Create a response through the OpenAI Responses API with retry handling."""
        if self._client is None:
            raise RuntimeError("OpenAI client is not configured")

        effective_model = model or self._model
        last_error: Exception | None = None

        for attempt in range(max_retries + 1):
            try:
                return await self._client.responses_create(
                    model=effective_model,
                    input=input_text,
                    temperature=temperature,
                    timeout=timeout,
                    **kwargs,
                )
            except Exception as exc:  # pragma: no cover - wrapper boundary
                last_error = exc
                if attempt >= max_retries:
                    raise
                await asyncio.sleep(0.5 * (attempt + 1))

        if last_error is not None:
            raise last_error

        raise RuntimeError("OpenAI response generation failed")
