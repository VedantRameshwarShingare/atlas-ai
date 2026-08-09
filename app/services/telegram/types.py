"""Typed Telegram webhook payload models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class TelegramUserPayload(BaseModel):
    """Telegram sender metadata."""

    id: int
    is_bot: bool | None = None
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None


class TelegramChatPayload(BaseModel):
    """Telegram chat metadata."""

    id: int
    type: str


class TelegramMessagePayload(BaseModel):
    """Telegram message payload used by the webhook."""

    model_config = ConfigDict(populate_by_name=True)

    message_id: int | None = None
    chat: TelegramChatPayload
    text: str | None = None
    caption: str | None = None
    from_user: TelegramUserPayload | None = Field(default=None, alias="from")


class TelegramUpdatePayload(BaseModel):
    """Top-level Telegram update payload."""

    update_id: int | None = None
    message: TelegramMessagePayload | None = None
