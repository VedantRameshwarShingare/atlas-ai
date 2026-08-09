"""HTTP client abstraction for Telegram Bot API operations."""

from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings
from app.core.logging import get_logger
from app.services.telegram.exceptions import (
    TelegramConfigurationError,
    TelegramProviderUnavailableError,
    TelegramRateLimitError,
    TelegramUnauthorizedError,
    TelegramValidationError,
)


class TelegramClient:
    """Wrap Telegram Bot API operations behind a typed async client."""

    _base_url = "https://api.telegram.org"

    def __init__(
        self,
        *,
        bot_token: str | None = None,
        timeout_seconds: float | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        configured_token = settings.telegram.bot_token.get_secret_value() if settings.telegram.bot_token else None
        self._bot_token = bot_token or configured_token
        self._timeout_seconds = timeout_seconds or settings.telegram.request_timeout_seconds
        self._client = http_client or httpx.AsyncClient(base_url=self._base_url)
        self._logger = get_logger(__name__)

    async def send_message(self, *, chat_id: int, text: str) -> dict[str, Any]:
        """Send a plain-text message to a Telegram chat."""
        payload = await self._request_json("POST", "sendMessage", {"chat_id": chat_id, "text": text})
        result = payload.get("result")
        if not isinstance(result, dict):
            raise TelegramValidationError("Telegram sendMessage response was invalid")
        return result

    async def get_webhook_info(self) -> dict[str, Any]:
        """Return current webhook metadata."""
        payload = await self._request_json("GET", "getWebhookInfo")
        result = payload.get("result")
        if not isinstance(result, dict):
            raise TelegramValidationError("Telegram getWebhookInfo response was invalid")
        return result

    async def set_webhook(self, *, url: str, secret_token: str | None = None) -> dict[str, Any]:
        """Register a webhook URL with Telegram."""
        payload: dict[str, Any] = {"url": url}
        if secret_token:
            payload["secret_token"] = secret_token
        return await self._request_json("POST", "setWebhook", payload)

    async def delete_webhook(self) -> dict[str, Any]:
        """Delete the configured webhook from Telegram."""
        return await self._request_json("POST", "deleteWebhook", {})

    async def _request_json(
        self,
        method: str,
        operation: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        token = self._require_bot_token()
        path = f"/bot{token}/{operation}"

        try:
            if method == "GET":
                response = await self._client.get(path, timeout=self._timeout_seconds, params=payload)
            else:
                response = await self._client.post(path, timeout=self._timeout_seconds, json=payload)
        except httpx.TimeoutException as exc:
            self._logger.warning("telegram_request_timeout operation={operation}", operation=operation)
            raise TelegramProviderUnavailableError("Telegram request timed out") from exc
        except httpx.HTTPError as exc:
            self._logger.warning("telegram_request_failed operation={operation}", operation=operation)
            raise TelegramProviderUnavailableError("Telegram request failed") from exc

        if response.status_code in {401, 403}:
            raise TelegramUnauthorizedError("Telegram authentication failed")
        if response.status_code == 429:
            raise TelegramRateLimitError("Telegram rate limit exceeded")
        if response.status_code >= 500:
            raise TelegramProviderUnavailableError("Telegram service is unavailable")
        if response.status_code >= 400:
            raise TelegramProviderUnavailableError("Telegram request failed")

        try:
            data = response.json()
        except ValueError as exc:
            raise TelegramValidationError("Telegram returned invalid JSON") from exc

        if not isinstance(data, dict):
            raise TelegramValidationError("Telegram response format was invalid")
        if data.get("ok") is not True:
            description = str(data.get("description") or "Telegram request failed")
            if "unauthorized" in description.lower():
                raise TelegramUnauthorizedError("Telegram authentication failed")
            raise TelegramProviderUnavailableError("Telegram request failed")

        return data

    def _require_bot_token(self) -> str:
        if not self._bot_token:
            raise TelegramConfigurationError("Telegram bot token is not configured")
        return self._bot_token
