"""Async provider mocks used by tests; none make external calls."""

from __future__ import annotations

from typing import Any


class AsyncProviderMock:
    def __init__(self, response: Any = None) -> None:
        self.response = response if response is not None else {"status": "ok"}
        self.calls: list[tuple[str, dict[str, Any]]] = []

    async def request(self, operation: str = "request", **kwargs: Any) -> Any:
        self.calls.append((operation, kwargs))
        return self.response

    async def ping(self) -> dict[str, bool]:
        self.calls.append(("ping", {}))
        return {"available": True}


class MockOpenAI(AsyncProviderMock):
    pass


class MockFinnhub(AsyncProviderMock):
    pass


class MockYahoo(AsyncProviderMock):
    pass


class MockSEC(AsyncProviderMock):
    pass


class MockTelegram(AsyncProviderMock):
    pass


class MockChromaDB(AsyncProviderMock):
    pass


class MockDatabase(AsyncProviderMock):
    async def execute(self, statement: Any, **kwargs: Any) -> Any:
        return await self.request("execute", statement=statement, **kwargs)
