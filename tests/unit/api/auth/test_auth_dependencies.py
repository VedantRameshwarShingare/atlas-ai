"""Tests for JWT authentication dependencies."""

from uuid import uuid4

from app.core.security.jwt import create_access_token, decode_access_token


def test_create_and_decode_access_token() -> None:
    """A generated access token should decode to the original user ID."""

    user_id = uuid4()

    token = create_access_token(user_id)

    assert token
    assert decode_access_token(token) == user_id


def test_access_token_contains_user_identity() -> None:
    """The JWT should contain the user's identity."""

    user_id = uuid4()

    token = create_access_token(user_id)

    decoded_user_id = decode_access_token(token)

    assert decoded_user_id == user_id
