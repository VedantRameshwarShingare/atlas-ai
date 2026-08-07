"""Skeleton for async HTTP API integration coverage."""
import pytest

@pytest.mark.asyncio
async def test_api_client_is_available(api_client) -> None:
    assert api_client.base_url.host == "test"
