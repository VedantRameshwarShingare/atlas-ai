"""Chat persistence and orchestration service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.orchestrator import AtlasOrchestrator
from app.ai.types import ChatRequest, ChatResponse
from app.core.config import settings
from app.core.exceptions import ConversationNotFoundError, ProviderConfigurationError, ProviderUnavailableError
from app.core.logging import get_logger
from app.models.conversation import Conversation
from app.models.message import Message
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.user_repository import UserRepository
from app.services.base import BaseService


class ChatService(BaseService):
    """Coordinate chat persistence and AI response generation."""

    name = "chat"
    description = "Persists conversations and messages and coordinates AI responses."

    def __init__(
        self,
        session: AsyncSession,
        orchestrator: AtlasOrchestrator | None = None,
        history_limit: int | None = None,
    ) -> None:
        super().__init__()

        self._user_repository = UserRepository(session)
        self._conversation_repository = ConversationRepository(session)
        self._message_repository = MessageRepository(session)
        self._orchestrator = orchestrator or AtlasOrchestrator()
        self._history_limit = history_limit or settings.chat.history_limit
        self._logger = get_logger(__name__)

    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Persist the user message, generate an AI response, and persist it."""

        if request.user_id is None:
            raise ValueError("user_id is required for persisted chat")

        logger = getattr(self, "_logger", None)

        user = await self._user_repository.get(request.user_id)

        if user is None:
            raise ValueError(f"User {request.user_id} was not found")

        conversation = await self._get_or_create_conversation(
            user_id=request.user_id,
            conversation_id=request.conversation_id,
            title=request.text[:255],
        )

        history = await self._message_repository.list_by_conversation(
            conversation.id,
            limit=getattr(self, "_history_limit", settings.chat.history_limit),
        )

        user_message = Message(
            conversation_id=conversation.id,
            role="user",
            content=request.text,
            message_metadata=request.metadata,
        )

        await self._message_repository.create(user_message)

        request_with_history = ChatRequest(
            user_id=request.user_id,
            text=request.text,
            conversation_id=conversation.id,
            metadata=request.metadata,
            conversation_history=[
                {
                    "role": message.role,
                    "content": message.content,
                }
                for message in history
            ],
        )

        if logger is not None:
            logger.info("chat_orchestration_started conversation_id={conversation_id}", conversation_id=conversation.id)
        try:
            response = await self._orchestrator.handle_request(request_with_history)
        except (ProviderConfigurationError, ProviderUnavailableError):
            if logger is not None:
                logger.warning(
                    "chat_orchestration_failed conversation_id={conversation_id}",
                    conversation_id=conversation.id,
                )
            raise
        except Exception as exc:
            if logger is not None:
                logger.exception(
                    "chat_orchestration_failed conversation_id={conversation_id}",
                    conversation_id=conversation.id,
                )
            raise ProviderUnavailableError("The AI provider is currently unavailable") from exc

        assistant_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=response.content,
            message_metadata={
                "response_type": response.response_type.value,
                "sources": response.sources,
                "tool_citations": response.tool_citations,
            },
        )

        await self._message_repository.create(assistant_message)

        conversation.last_message_at = datetime.now(UTC)

        await self._conversation_repository.update(conversation)

        response.metadata.update(
            {
                "conversation_id": str(conversation.id),
                "user_message_id": str(getattr(user_message, "id", "")),
                "assistant_message_id": str(getattr(assistant_message, "id", "")),
            }
        )
        if logger is not None:
            logger.info("chat_completed conversation_id={conversation_id}", conversation_id=conversation.id)

        return response

    async def get_conversation(self, *, user_id: UUID, conversation_id: UUID) -> Conversation:
        """Return a conversation only when it belongs to the authenticated user."""
        return await self._get_owned_conversation(user_id=user_id, conversation_id=conversation_id)

    async def list_messages(self, *, user_id: UUID, conversation_id: UUID) -> list[Message]:
        """Return bounded chronological messages for an owned conversation."""
        conversation = await self._get_owned_conversation(user_id=user_id, conversation_id=conversation_id)
        return await self._message_repository.list_by_conversation(conversation.id, limit=self._history_limit)

    async def delete_conversation(self, *, user_id: UUID, conversation_id: UUID) -> None:
        """Delete an owned conversation and its cascade-associated messages."""
        conversation = await self._get_owned_conversation(user_id=user_id, conversation_id=conversation_id)
        await self._conversation_repository.delete(conversation)

    async def _get_or_create_conversation(
        self,
        *,
        user_id: UUID,
        conversation_id: UUID | None,
        title: str,
    ) -> Conversation:
        """Get an existing conversation or create a new one."""

        if conversation_id is not None:
            return await self._get_owned_conversation(user_id=user_id, conversation_id=conversation_id)

        conversation = Conversation(
            user_id=user_id,
            title=title,
            status="active",
            last_message_at=datetime.now(UTC),
        )

        return await self._conversation_repository.create(conversation)

    async def _get_owned_conversation(self, *, user_id: UUID, conversation_id: UUID) -> Conversation:
        """Resolve an owned conversation without revealing unavailable conversation IDs."""
        conversation = await self._conversation_repository.get(conversation_id)
        if conversation is None or conversation.user_id != user_id:
            raise ConversationNotFoundError("Conversation was not found")
        return conversation

    async def ping(self) -> dict[str, Any]:
        """Return service readiness metadata."""

        return {
            "service": self.name,
            "available": True,
        }
