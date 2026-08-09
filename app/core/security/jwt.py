"""JWT creation and verification utilities."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from jwt import InvalidTokenError

from app.core.config import settings

_TELEGRAM_LINK_TOKEN_MINUTES = 10


def _get_jwt_secret() -> str:
    """Return configured JWT signing secret or fail with a controlled error."""
    if settings.auth.jwt_secret_key is None:
        raise ValueError("JWT secret key is not configured")
    return settings.auth.jwt_secret_key.get_secret_value()


def create_access_token(user_id: UUID) -> str:
    """Create a signed JWT access token for a user."""
    return _create_token(user_id=user_id, token_type="access", expires_at=_access_expiration())


def create_telegram_link_token(user_id: UUID) -> str:
    """Create a short-lived signed token for linking Telegram to an account."""
    now = datetime.now(UTC)
    expires_at = now + timedelta(minutes=_TELEGRAM_LINK_TOKEN_MINUTES)
    return _create_token(user_id=user_id, token_type="telegram_link", expires_at=expires_at)


def decode_telegram_link_token(token: str) -> UUID:
    """Decode and validate a Telegram account-link token."""
    return _decode_token(token=token, expected_type="telegram_link", error_label="Telegram link token")


def telegram_link_token_ttl_seconds() -> int:
    """Return the Telegram link-token lifetime in seconds."""
    return _TELEGRAM_LINK_TOKEN_MINUTES * 60


def _access_expiration() -> datetime:
    now = datetime.now(UTC)
    return now + timedelta(minutes=settings.auth.access_token_expire_minutes)


def _create_token(*, user_id: UUID, token_type: str, expires_at: datetime) -> str:
    """Create a signed typed JWT token."""
    now = datetime.now(UTC)

    payload = {
        "sub": str(user_id),
        "type": token_type,
        "iat": now,
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        _get_jwt_secret(),
        algorithm=settings.auth.jwt_algorithm,
    )


def decode_access_token(token: str) -> UUID:
    """Decode and validate a JWT access token."""
    return _decode_token(token=token, expected_type="access", error_label="access token")


def _decode_token(*, token: str, expected_type: str, error_label: str) -> UUID:
    """Decode and validate a typed JWT token."""
    try:
        payload = jwt.decode(
            token,
            _get_jwt_secret(),
            algorithms=[settings.auth.jwt_algorithm],
        )
    except InvalidTokenError as exc:
        raise ValueError(f"Invalid {error_label}") from exc

    subject = payload.get("sub")
    token_type = payload.get("type")

    if token_type != expected_type:
        raise ValueError(f"Token is not a valid {error_label}")

    if not isinstance(subject, str) or not subject:
        raise ValueError("Token does not contain a user ID")

    try:
        return UUID(subject)
    except ValueError as exc:
        raise ValueError("Token contains an invalid user ID") from exc
