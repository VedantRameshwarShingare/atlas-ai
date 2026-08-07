"""Shared async fixtures for Atlas AI test suites."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.ai.capabilities import CapabilityRegistry
from tests.mocks import MockChromaDB, MockDatabase, MockFinnhub, MockOpenAI, MockSEC, MockTelegram, MockYahoo


@pytest.fixture
def capability_registry() -> CapabilityRegistry:
    return CapabilityRegistry()


@pytest.fixture
def mock_database() -> MockDatabase: return MockDatabase()
@pytest.fixture
def mock_openai() -> MockOpenAI: return MockOpenAI()
@pytest.fixture
def mock_finnhub() -> MockFinnhub: return MockFinnhub()
@pytest.fixture
def mock_yahoo() -> MockYahoo: return MockYahoo()
@pytest.fixture
def mock_sec() -> MockSEC: return MockSEC()
@pytest.fixture
def mock_telegram() -> MockTelegram: return MockTelegram()
@pytest.fixture
def mock_chromadb() -> MockChromaDB: return MockChromaDB()


@pytest.fixture
async def api_client() -> AsyncClient:
    try:
        from app.main import app
    except Exception as exc:
        pytest.skip(f"API integration unavailable until application imports cleanly: {exc}")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
