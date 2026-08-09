"""HTTP-level chat hardening coverage using the injected fake orchestrator."""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_orchestrator
from app.core.exceptions import ProviderUnavailableError
from app.core.security.jwt import create_access_token
from app.models.user import User


async def _create_user(session: AsyncSession, *, label: str) -> User:
    """Persist a user suitable for authenticated API tests."""
    user = User(
        telegram_user_id=f"chat_{label}_{uuid4().hex[:10]}",
        username=f"chat_{label}",
        first_name="Chat",
        last_name="Tester",
        language="en",
        timezone="UTC",
        is_active=True,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


def _headers(user: User) -> dict[str, str]:
    """Return bearer authentication headers for a persisted user."""
    return {"Authorization": f"Bearer {create_access_token(user.id)}"}


@pytest.mark.asyncio
async def test_chat_persists_identifiers_and_returns_ordered_history(
    api_client: AsyncClient, db_session: AsyncSession
) -> None:
    """A second turn receives and exposes deterministic prior conversation history."""
    user = await _create_user(db_session, label="history")
    first = await api_client.post("/chat", headers=_headers(user), json={"text": "What is Python?"})

    assert first.status_code == 200
    first_data = first.json()["data"]
    conversation_id = UUID(first_data["conversation_id"])
    assert UUID(first_data["user_message_id"])
    assert UUID(first_data["assistant_message_id"])

    second = await api_client.post(
        "/chat",
        headers=_headers(user),
        json={"text": "What can I build with it?", "conversation_id": str(conversation_id)},
    )
    assert second.status_code == 200

    messages = await api_client.get(f"/conversations/{conversation_id}/messages", headers=_headers(user))
    assert messages.status_code == 200
    assert [message["role"] for message in messages.json()["data"]["messages"]] == [
        "user",
        "assistant",
        "user",
        "assistant",
    ]


@pytest.mark.asyncio
async def test_conversation_access_is_ownership_safe(api_client: AsyncClient, db_session: AsyncSession) -> None:
    """Another authenticated user receives a not-found response for a private conversation."""
    owner = await _create_user(db_session, label="owner")
    other = await _create_user(db_session, label="other")
    created = await api_client.post("/chat", headers=_headers(owner), json={"text": "Private conversation"})
    conversation_id = created.json()["data"]["conversation_id"]

    response = await api_client.get(f"/conversations/{conversation_id}", headers=_headers(other))

    assert response.status_code == 404
    assert response.json()["error"] == "conversation_not_found"


@pytest.mark.asyncio
async def test_chat_rejects_blank_and_nonexistent_conversation(
    api_client: AsyncClient, db_session: AsyncSession
) -> None:
    """Normal malformed input and unknown conversations produce controlled client errors."""
    user = await _create_user(db_session, label="validation")
    headers = _headers(user)

    blank = await api_client.post("/chat", headers=headers, json={"text": "   "})
    missing = await api_client.post(
        "/chat",
        headers=headers,
        json={"text": "Hello", "conversation_id": str(uuid4())},
    )

    assert blank.status_code == 422
    assert missing.status_code == 404


@pytest.mark.asyncio
async def test_deleted_conversation_is_not_available(api_client: AsyncClient, db_session: AsyncSession) -> None:
    """Deleting an owned conversation makes later reads return the safe not-found response."""
    user = await _create_user(db_session, label="delete")
    headers = _headers(user)
    created = await api_client.post("/chat", headers=headers, json={"text": "Delete this"})
    conversation_id = created.json()["data"]["conversation_id"]

    deleted = await api_client.delete(f"/conversations/{conversation_id}", headers=headers)
    missing = await api_client.get(f"/conversations/{conversation_id}", headers=headers)

    assert deleted.status_code == 200
    assert missing.status_code == 404


@pytest.mark.asyncio
async def test_provider_failure_returns_safe_service_error(api_client: AsyncClient, db_session: AsyncSession) -> None:
    """The chat endpoint hides provider internals while reporting a retryable failure."""
    from app.main import app

    class FailingOrchestrator:
        """Deterministically model a configured provider outage."""

        async def handle_request(self, request: object) -> object:
            """Raise the application-level provider failure."""
            raise ProviderUnavailableError("provider socket details")

    original_orchestrator = app.dependency_overrides[get_orchestrator]
    app.dependency_overrides[get_orchestrator] = FailingOrchestrator
    try:
        user = await _create_user(db_session, label="provider")
        response = await api_client.post("/chat", headers=_headers(user), json={"text": "Hello"})
    finally:
        app.dependency_overrides[get_orchestrator] = original_orchestrator

    assert response.status_code == 503
    assert response.json()["error"] == "provider_unavailable"
    assert "socket" not in response.text
