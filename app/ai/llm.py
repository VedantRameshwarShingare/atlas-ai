"""Async OpenAI Responses API wrapper."""

from __future__ import annotations

import asyncio
from typing import Any, Protocol

from openai import AsyncOpenAI

from app.core.config import settings
from app.core.exceptions import ProviderConfigurationError, ProviderUnavailableError


class SupportsResponsesAPI(Protocol):
    """Protocol describing the minimal OpenAI client surface used by the wrapper."""

    async def responses_create(self, **kwargs: Any) -> Any:
        """Create a response through the OpenAI Responses API."""


class _OpenAIResponsesAdapter:
    """Adapt the OpenAI SDK to the internal Responses API protocol."""

    def __init__(self, client: AsyncOpenAI) -> None:
        self._client = client

    async def responses_create(self, **kwargs: Any) -> Any:
        """Create a response using the OpenAI SDK."""

        return await self._client.responses.create(**kwargs)


class OpenAIClient:
    """Central wrapper for all OpenAI API calls."""

    def __init__(self, client: SupportsResponsesAPI | None = None) -> None:
        self._model = settings.openai.model
        self._api_key = settings.openai.api_key

        if client is not None:
            self._client = client
        elif self._api_key is not None:
            sdk_client = AsyncOpenAI(
                api_key=self._api_key.get_secret_value(),
                base_url=settings.openai.base_url,
            )
            self._client = _OpenAIResponsesAdapter(sdk_client)
        else:
            self._client = None

    async def create_response(
        self,
        *,
        model: str | None = None,
        input_text: str | None = None,
        temperature: float = 0.2,
        request_timeout: float = 30.0,
        max_retries: int = 2,
        **kwargs: Any,
    ) -> Any:
        """Create a response through the OpenAI Responses API."""

        if self._client is None:
            raise ProviderConfigurationError("The AI provider is not configured")

        effective_model = model or self._model
        last_error: Exception | None = None

        for attempt in range(max_retries + 1):
            try:
                async with asyncio.timeout(request_timeout):
                    return await self._client.responses_create(
                        model=effective_model,
                        input=input_text,
                        temperature=temperature,
                        **kwargs,
                    )
            except ProviderConfigurationError:
                raise
            except Exception as exc:
                last_error = exc

                if attempt >= max_retries:
                    raise ProviderUnavailableError("The AI provider is currently unavailable") from exc

                await asyncio.sleep(0.5 * (attempt + 1))

        if last_error is not None:
            raise last_error

        raise ProviderUnavailableError("The AI provider returned no response")
