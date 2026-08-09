"""Unit coverage for safe LLM configuration failures."""

from __future__ import annotations

import pytest

from app.ai.llm import OpenAIClient
from app.core.exceptions import ProviderConfigurationError


@pytest.mark.asyncio
async def test_missing_llm_client_raises_controlled_configuration_error() -> None:
    """A missing API key/client is not exposed as a raw SDK failure."""
    client = OpenAIClient.__new__(OpenAIClient)
    client._client = None

    with pytest.raises(ProviderConfigurationError, match="not configured"):
        await client.create_response(input_text="hello")
