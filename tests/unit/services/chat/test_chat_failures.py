"""Failure-boundary tests for the chat orchestration service."""

from __future__ import annotations

from uuid import uuid4

import pytest

from app.ai.types import ChatRequest
from app.core.exceptions import ProviderUnavailableError
from app.models.conversation import Conversation
from app.services.chat.chat import ChatService


class FakeUserRepository:
    """Return a known user without using a database."""

    async def get(self, user_id: object) -> object:
        """Return an object matching the requested identity."""
        return type("User", (), {"id": user_id})()


class FakeConversationRepository:
    """Provide a fixed conversation for service tests."""

    def __init__(self, conversation: Conversation) -> None:
        self.conversation = conversation

    async def get(self, conversation_id: object) -> Conversation:
        """Return the configured conversation."""
        return self.conversation

    async def update(self, conversation: Conversation) -> Conversation:
        """Return the updated conversation."""
        return conversation


class FakeMessageRepository:
    """Record persisted messages without committing data."""

    def __init__(self) -> None:
        self.created: list[object] = []

    async def list_by_conversation(self, conversation_id: object, *, limit: int) -> list[object]:
        """Return no previous messages."""
        return []

    async def create(self, message: object) -> object:
        """Record a message creation request."""
        self.created.append(message)
        return message


class FailingOrchestrator:
    """Simulate a provider failure after the user message is persisted."""

    async def handle_request(self, request: ChatRequest) -> object:
        """Raise an opaque provider-style exception."""
        raise TimeoutError("provider timeout")


@pytest.mark.asyncio
async def test_provider_failure_keeps_user_message_and_hides_provider_details() -> None:
    """User input is retained while an unsafe provider error becomes controlled."""
    user_id = uuid4()
    conversation_id = uuid4()
    conversation = Conversation(user_id=user_id, title="Test", status="active")
    messages = FakeMessageRepository()
    service = ChatService.__new__(ChatService)
    service._user_repository = FakeUserRepository()
    service._conversation_repository = FakeConversationRepository(conversation)
    service._message_repository = messages
    service._orchestrator = FailingOrchestrator()
    service._history_limit = 20

    with pytest.raises(ProviderUnavailableError, match="currently unavailable"):
        await service.chat(ChatRequest(user_id=user_id, text="Hello", conversation_id=conversation_id))

    assert len(messages.created) == 1
    assert messages.created[0].role == "user"
