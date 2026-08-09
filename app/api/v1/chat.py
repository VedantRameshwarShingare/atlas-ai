"""Chat endpoint for the API layer."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel, Field, field_validator

from app.ai.types import ChatRequest
from app.api.dependencies import (
    ChatServiceDependency,
    CurrentUserDependency,
)
from app.api.responses import APIResponse

router = APIRouter(tags=["chat"])


class ChatRequestPayload(BaseModel):
    """Validated public payload for an authenticated chat request."""

    text: str = Field(min_length=1, max_length=8_000)
    conversation_id: UUID | None = None
    metadata: dict[str, object] = Field(default_factory=dict)

    @field_validator("text")
    @classmethod
    def require_non_blank_text(cls, value: str) -> str:
        """Reject whitespace-only requests before persistence or provider calls."""
        normalized = value.strip()
        if not normalized:
            raise ValueError("text must not be blank")
        return normalized


@router.post("/chat", response_model=APIResponse)
async def chat(
    request: ChatRequestPayload,
    current_user: CurrentUserDependency,
    chat_service: ChatServiceDependency,
) -> APIResponse:
    """Persist a chat request and return the generated AI response."""

    chat_request = ChatRequest(
        user_id=current_user.id,
        text=request.text,
        conversation_id=request.conversation_id,
        metadata=request.metadata,
    )

    response = await chat_service.chat(chat_request)

    return APIResponse(
        data={
            "content": response.content,
            "response_type": response.response_type.value,
            **response.metadata,
        },
        metadata={
            "sources": response.sources,
            "tool_citations": response.tool_citations,
        },
    )


@router.get("/conversations/{conversation_id}", response_model=APIResponse)
async def get_conversation(
    conversation_id: UUID,
    current_user: CurrentUserDependency,
    chat_service: ChatServiceDependency,
) -> APIResponse:
    """Return an authenticated user's conversation metadata."""
    conversation = await chat_service.get_conversation(user_id=current_user.id, conversation_id=conversation_id)
    return APIResponse(
        data={
            "conversation_id": str(conversation.id),
            "title": conversation.title,
            "status": conversation.status,
        }
    )


@router.get("/conversations/{conversation_id}/messages", response_model=APIResponse)
async def list_conversation_messages(
    conversation_id: UUID,
    current_user: CurrentUserDependency,
    chat_service: ChatServiceDependency,
) -> APIResponse:
    """Return an authenticated user's bounded chronological conversation history."""
    messages = await chat_service.list_messages(user_id=current_user.id, conversation_id=conversation_id)
    return APIResponse(
        data={
            "conversation_id": str(conversation_id),
            "messages": [
                {"message_id": str(message.id), "role": message.role, "content": message.content}
                for message in messages
            ],
        }
    )


@router.delete("/conversations/{conversation_id}", response_model=APIResponse)
async def delete_conversation(
    conversation_id: UUID,
    current_user: CurrentUserDependency,
    chat_service: ChatServiceDependency,
) -> APIResponse:
    """Delete an authenticated user's conversation and associated messages."""
    await chat_service.delete_conversation(user_id=current_user.id, conversation_id=conversation_id)
    return APIResponse(data={"conversation_id": str(conversation_id), "status": "deleted"})
