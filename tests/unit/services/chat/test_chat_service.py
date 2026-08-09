"""Unit tests for the chat persistence service."""

from uuid import uuid4

import pytest

from app.ai.types import ChatRequest, ChatResponse
from app.models.conversation import Conversation
from app.services.chat.chat import ChatService


class FakeUserRepository:
    def __init__(self, user):
        self.user = user

    async def get(self, user_id):
        return self.user


class FakeConversationRepository:
    def __init__(self, conversation=None):
        self.conversation = conversation
        self.created = None
        self.updated = None

    async def get(self, conversation_id):
        return self.conversation

    async def create(self, conversation):
        self.created = conversation
        return conversation

    async def update(self, conversation):
        self.updated = conversation
        return conversation


class FakeMessageRepository:
    def __init__(self, history=None):
        self.history = history or []
        self.created = []

    async def list_by_conversation(self, conversation_id, *, limit=50):
        return self.history

    async def create(self, message):
        self.created.append(message)
        return message


class FakeOrchestrator:
    def __init__(self):
        self.request = None

    async def handle_request(self, request):
        self.request = request

        return ChatResponse(
            content="Your favorite language is Python.",
        )


class FakeUser:
    def __init__(self, user_id):
        self.id = user_id


@pytest.mark.asyncio
async def test_chat_uses_previous_conversation_history():
    user_id = uuid4()
    conversation_id = uuid4()

    conversation = Conversation(
        user_id=user_id,
        title="Previous conversation",
        status="active",
    )

    history_message = type(
        "HistoryMessage",
        (),
        {
            "role": "user",
            "content": "My favorite programming language is Python.",
        },
    )()

    orchestrator = FakeOrchestrator()

    service = ChatService.__new__(ChatService)

    service._user_repository = FakeUserRepository(FakeUser(user_id))
    service._conversation_repository = FakeConversationRepository(conversation)
    service._message_repository = FakeMessageRepository([history_message])
    service._orchestrator = orchestrator

    request = ChatRequest(
        user_id=user_id,
        text="What is my favorite programming language?",
        conversation_id=conversation_id,
    )

    response = await service.chat(request)

    assert response.content == "Your favorite language is Python."

    assert orchestrator.request is not None
    assert len(orchestrator.request.conversation_history) == 1

    assert orchestrator.request.conversation_history[0]["content"] == "My favorite programming language is Python."
