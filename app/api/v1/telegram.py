"""Telegram webhook endpoints that reuse the existing Atlas chat stack."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.responses import APIResponse
from app.database.session import get_async_session
from app.services.chat.chat import ChatService
from app.services.telegram.client import TelegramClient
from app.services.telegram.exceptions import (
    TelegramConfigurationError,
    TelegramProviderUnavailableError,
    TelegramRateLimitError,
    TelegramUnauthorizedError,
    TelegramValidationError,
)
from app.services.telegram.service import TelegramService
from app.services.telegram.types import TelegramUpdatePayload

router = APIRouter(prefix="/telegram", tags=["telegram"])


def get_telegram_service(session: AsyncSession = Depends(get_async_session)) -> TelegramService:
    """Provide the Telegram webhook service using the existing chat service."""
    return TelegramService(session, chat_service=ChatService(session), telegram_client=TelegramClient())


def _handle_telegram_error(exc: Exception) -> HTTPException:
    if isinstance(exc, TelegramUnauthorizedError):
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Telegram webhook secret")
    if isinstance(exc, TelegramConfigurationError):
        return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Telegram is not configured")
    if isinstance(exc, TelegramRateLimitError):
        return HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Telegram rate limit exceeded")
    if isinstance(exc, TelegramValidationError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if isinstance(exc, TelegramProviderUnavailableError):
        return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Telegram is unavailable")
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Telegram operation failed")


@router.post("/webhook", response_model=APIResponse)
async def telegram_webhook(
    payload: TelegramUpdatePayload,
    service: TelegramService = Depends(get_telegram_service),
    secret_token: Annotated[str | None, Header(alias="X-Telegram-Bot-Api-Secret-Token")] = None,
) -> APIResponse:
    """Receive a Telegram update and route it through the existing Atlas services."""
    try:
        result = await service.process_update(payload, webhook_secret=secret_token)
    except Exception as exc:
        raise _handle_telegram_error(exc) from exc
    return APIResponse(data=result)
