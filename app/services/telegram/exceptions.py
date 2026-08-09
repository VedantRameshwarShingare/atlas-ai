"""Telegram-domain exceptions and HTTP normalization."""

from __future__ import annotations


class TelegramError(Exception):
    """Base Telegram-domain error."""


class TelegramConfigurationError(TelegramError):
    """Raised when Telegram configuration is missing or invalid."""


class TelegramUnauthorizedError(TelegramError):
    """Raised for invalid Telegram bot credentials or webhook secrets."""


class TelegramRateLimitError(TelegramError):
    """Raised when Telegram rate limits a request."""


class TelegramProviderUnavailableError(TelegramError):
    """Raised when Telegram is unavailable or times out."""


class TelegramValidationError(TelegramError):
    """Raised when Telegram payloads are malformed for the expected operation."""


class TelegramLinkError(TelegramError):
    """Raised when Telegram account linking cannot be completed safely."""
