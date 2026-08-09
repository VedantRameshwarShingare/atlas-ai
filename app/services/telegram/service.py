"""Telegram webhook service that reuses the existing Atlas chat stack."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.types import ChatRequest, ChatResponse
from app.core.config import settings
from app.core.logging import get_logger
from app.core.security.jwt import decode_telegram_link_token
from app.models.conversation import Conversation
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.user_repository import UserRepository
from app.services.chat.chat import ChatService
from app.services.telegram.client import TelegramClient
from app.services.telegram.exceptions import (
    TelegramLinkError,
    TelegramUnauthorizedError,
)
from app.services.telegram.formatter import TelegramFormatter
from app.services.telegram.types import (
    TelegramUpdatePayload,
    TelegramUserPayload,
)


class TelegramService:
    """Process Telegram webhook updates through the existing Atlas chat architecture."""

    conversation_title = "[telegram] private chat"

    def __init__(
        self,
        session: AsyncSession,
        *,
        chat_service: ChatService,
        telegram_client: TelegramClient | None = None,
        formatter: TelegramFormatter | None = None,
    ) -> None:
        self._session = session
        self._chat_service = chat_service
        self._client = telegram_client or TelegramClient()
        self._formatter = formatter or TelegramFormatter()
        self._users = UserRepository(session)
        self._conversations = ConversationRepository(session)
        self._logger = get_logger(__name__)

    async def process_update(
        self,
        update: TelegramUpdatePayload,
        *,
        webhook_secret: str | None = None,
    ) -> dict[str, object]:
        """Process one Telegram update and return a safe status payload."""
        self._validate_webhook_secret(webhook_secret)

        message = update.message

        if message is None:
            return {
                "status": "ignored",
                "reason": "no_message",
            }

        chat_id = message.chat.id

        if message.chat.type != "private":
            await self._client.send_message(
                chat_id=chat_id,
                text="Only private Telegram chats are supported right now.",
            )
            return {
                "status": "ignored",
                "reason": "unsupported_chat_type",
            }

        telegram_user = message.from_user

        if telegram_user is None:
            await self._client.send_message(
                chat_id=chat_id,
                text=self._linking_instructions(),
            )
            return {
                "status": "ignored",
                "reason": "missing_user",
            }

        text = (message.text or "").strip()

        if not text:
            await self._client.send_message(
                chat_id=chat_id,
                text="Only text messages are supported right now.",
            )
            return {
                "status": "ignored",
                "reason": "missing_text",
            }

        try:
            return await self._process_text_message(
                chat_id=chat_id,
                telegram_user=telegram_user,
                text=text,
            )
        except TelegramLinkError as exc:
            await self._client.send_message(
                chat_id=chat_id,
                text=str(exc),
            )
            return {
                "status": "rejected",
                "reason": "link_failed",
            }
        except Exception:
            self._logger.exception(
                "telegram_update_processing_failed",
            )
            await self._client.send_message(
                chat_id=chat_id,
                text=("Sorry, I couldn't process that request right now. Please try again."),
            )
            return {
                "status": "handled_with_error",
            }

    async def _process_text_message(
        self,
        *,
        chat_id: int,
        telegram_user: TelegramUserPayload,
        text: str,
    ) -> dict[str, object]:
        command, argument = self._split_command(text)
        telegram_user_id = str(telegram_user.id)

        linked_user = await self._users.get_by_telegram_user_id(
            telegram_user_id,
        )

        if command in {"/start", "/link"}:
            return await self._handle_command(
                chat_id=chat_id,
                command=command,
                argument=argument,
                telegram_user=telegram_user,
                linked_user=linked_user,
            )

        if linked_user is None:
            await self._client.send_message(
                chat_id=chat_id,
                text=self._linking_instructions(),
            )
            return {
                "status": "rejected",
                "reason": "unlinked_user",
            }

        conversation = await self._get_or_create_conversation(
            linked_user.id,
        )

        response = await self._chat_service.chat(
            ChatRequest(
                user_id=linked_user.id,
                text=text,
                conversation_id=conversation.id,
                metadata={
                    "source": "telegram",
                    "telegram_chat_id": str(chat_id),
                    "telegram_user_id": telegram_user_id,
                },
            )
        )

        await self._send_chat_response(
            chat_id=chat_id,
            response=response,
        )

        return {
            "status": "processed",
            "conversation_id": str(conversation.id),
        }

    async def _handle_command(
        self,
        *,
        chat_id: int,
        command: str,
        argument: str | None,
        telegram_user: TelegramUserPayload,
        linked_user: object | None,
    ) -> dict[str, object]:
        if linked_user is not None:
            await self._client.send_message(
                chat_id=chat_id,
                text="Your Telegram account is connected.",
            )
            return {
                "status": "processed",
                "reason": "already_linked",
            }

        if argument:
            user = await self._link_account(
                argument,
                telegram_user,
            )

            await self._client.send_message(
                chat_id=chat_id,
                text="Your Telegram account is connected.",
            )

            return {
                "status": "processed",
                "linked_user_id": str(user.id),
            }

        await self._client.send_message(
            chat_id=chat_id,
            text=self._linking_instructions(),
        )

        return {
            "status": "processed",
            "reason": "link_instructions",
        }

    async def _link_account(
        self,
        token: str,
        telegram_user: TelegramUserPayload,
    ):
        telegram_user_id = str(telegram_user.id)

        user_id = decode_telegram_link_token(token)

        user = await self._users.get(user_id)

        if user is None:
            raise TelegramLinkError(
                "That Telegram linking code is invalid or expired.",
            )

        existing = await self._users.get_by_telegram_user_id(
            telegram_user_id,
        )

        if existing is not None and existing.id != user.id:
            raise TelegramLinkError(
                "This Telegram account is already linked to another Atlas account.",
            )

        if user.telegram_user_id and user.telegram_user_id != telegram_user_id:
            raise TelegramLinkError(
                "This Atlas account is already linked to a different Telegram account.",
            )

        user.telegram_user_id = telegram_user_id

        try:
            await self._users.update(user)
        except IntegrityError as exc:
            raise TelegramLinkError(
                "This Telegram account is already linked to another Atlas account.",
            ) from exc

        return user

    async def _get_or_create_conversation(
        self,
        user_id: UUID,
    ) -> Conversation:
        conversation = await self._conversations.get_latest_for_user(
            user_id,
            title=self.conversation_title,
        )

        if conversation is not None:
            return conversation

        conversation = Conversation(
            user_id=user_id,
            title=self.conversation_title,
            status="active",
            last_message_at=datetime.now(UTC),
        )

        return await self._conversations.create(conversation)

    async def _send_chat_response(
        self,
        *,
        chat_id: int,
        response: ChatResponse,
    ) -> None:
        chunks = await self._formatter.render_messages(response)

        for chunk in chunks:
            await self._client.send_message(
                chat_id=chat_id,
                text=chunk,
            )

    def _validate_webhook_secret(
        self,
        provided_secret: str | None,
    ) -> None:
        configured = settings.telegram.webhook_secret.get_secret_value() if settings.telegram.webhook_secret else None

        if configured is None:
            return

        if provided_secret != configured:
            raise TelegramUnauthorizedError(
                "Invalid Telegram webhook secret",
            )

    @staticmethod
    def _split_command(
        text: str,
    ) -> tuple[str | None, str | None]:
        if not text.startswith("/"):
            return None, None

        pieces = text.split(maxsplit=1)

        command = (
            pieces[0]
            .split(
                "@",
                maxsplit=1,
            )[0]
            .lower()
        )

        argument = pieces[1].strip() if len(pieces) > 1 else None

        return command, argument

    @staticmethod
    def _linking_instructions() -> str:
        return (
            "Your Telegram account is not connected yet. "
            "Sign in to Atlas, request a Telegram link token, "
            "then send /link <token> here."
        )
