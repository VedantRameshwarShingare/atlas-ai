"""Shared async fixtures for Atlas AI test suites."""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.capabilities import CapabilityRegistry
from app.ai.enums import ResponseType
from app.ai.types import ChatRequest, ChatResponse
from app.api.dependencies import get_orchestrator
from app.database.session import async_engine, async_session_factory
from tests.mocks import MockChromaDB, MockDatabase, MockFinnhub, MockOpenAI, MockSEC, MockTelegram, MockYahoo


@pytest.fixture
def capability_registry() -> CapabilityRegistry:
    return CapabilityRegistry()


@pytest.fixture
def mock_database() -> MockDatabase:
    return MockDatabase()


@pytest.fixture
def mock_openai() -> MockOpenAI:
    return MockOpenAI()


@pytest.fixture
def mock_finnhub() -> MockFinnhub:
    return MockFinnhub()


@pytest.fixture
def mock_yahoo() -> MockYahoo:
    return MockYahoo()


@pytest.fixture
def mock_sec() -> MockSEC:
    return MockSEC()


@pytest.fixture
def mock_telegram() -> MockTelegram:
    return MockTelegram()


@pytest.fixture
def mock_chromadb() -> MockChromaDB:
    return MockChromaDB()


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a real async database session for integration tests."""

    async with async_session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture(autouse=True)
async def dispose_database_pool_after_test() -> AsyncGenerator[None, None]:
    """Avoid reusing asyncpg connections across pytest's per-test event loops."""
    yield
    await async_engine.dispose()


@pytest.fixture
async def api_client() -> AsyncGenerator[AsyncClient, None]:
    """Provide an async HTTP client for API integration tests."""

    from app.main import app

    class FakeOrchestrator:
        """Deterministic orchestrator used by HTTP tests without provider calls."""

        async def handle_request(self, request: ChatRequest) -> ChatResponse:
            """Return a predictable response for a valid chat request."""
            return ChatResponse(content=f"Test response: {request.text}", response_type=ResponseType.MARKDOWN)

    app.dependency_overrides[get_orchestrator] = FakeOrchestrator

    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            yield client
    finally:
        app.dependency_overrides.pop(get_orchestrator, None)
