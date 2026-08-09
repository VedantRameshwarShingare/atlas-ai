"""Lightweight model factories for unit and integration tests."""

from __future__ import annotations

from typing import Any
from uuid import uuid4


def _record(values: dict[str, Any], overrides: dict[str, object]) -> dict[str, Any]:
    values.update(overrides)
    return values


def user_factory(**overrides: object) -> dict[str, Any]:
    values = {
        "id": str(uuid4()),
        "telegram_user_id": str(uuid4().int)[:12],
        "username": "atlas_test",
        "timezone": "UTC",
    }
    return _record(values, overrides)


def conversation_factory(*, user_id: str | None = None, **overrides: object) -> dict[str, Any]:
    values = {"id": str(uuid4()), "user_id": user_id or str(uuid4()), "title": "Test conversation", "status": "active"}
    return _record(values, overrides)


def workspace_factory(*, user_id: str | None = None, **overrides: object) -> dict[str, Any]:
    values = {"id": str(uuid4()), "user_id": user_id or str(uuid4()), "title": "Test workspace", "status": "active"}
    return _record(values, overrides)


def document_factory(*, user_id: str | None = None, **overrides: object) -> dict[str, Any]:
    values = {
        "id": str(uuid4()),
        "user_id": user_id or str(uuid4()),
        "filename": "test.pdf",
        "document_type": "pdf",
        "file_path": "/tmp/test.pdf",
        "status": "uploaded",
    }
    return _record(values, overrides)


def message_factory(*, conversation_id: str | None = None, **overrides: object) -> dict[str, Any]:
    values = {
        "id": str(uuid4()),
        "conversation_id": conversation_id or str(uuid4()),
        "role": "user",
        "content": "Test message",
        "metadata": {},
    }
    return _record(values, overrides)


def watchlist_factory(*, user_id: str | None = None, **overrides: object) -> dict[str, Any]:
    values = {
        "id": str(uuid4()),
        "user_id": user_id or str(uuid4()),
        "symbol": "ATLS",
        "company_name": "Atlas Inc.",
        "is_active": True,
    }
    return _record(values, overrides)


def alert_factory(*, user_id: str | None = None, **overrides: object) -> dict[str, Any]:
    values = {
        "id": str(uuid4()),
        "user_id": user_id or str(uuid4()),
        "alert_type": "price",
        "symbol": "ATLS",
        "condition": "price > 100",
        "is_enabled": True,
    }
    return _record(values, overrides)
