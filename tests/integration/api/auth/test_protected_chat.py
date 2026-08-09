"""Integration tests for JWT-protected chat."""

from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.jwt import create_access_token
from app.models.user import User


@pytest.mark.asyncio
async def test_chat_requires_authentication(
    api_client: AsyncClient,
) -> None:
    """Chat must reject requests without a JWT."""

    response = await api_client.post(
        "/chat",
        json={
            "user_id": str(uuid4()),
            "text": "Hello Atlas",
            "conversation_id": None,
            "metadata": {},
        },
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_chat_accepts_valid_jwt(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Chat must accept a JWT belonging to an existing user."""

    user = User(
        telegram_user_id=f"test_{uuid4().hex[:12]}",
        username="auth_test_user",
        first_name="Auth",
        last_name="Test",
        language="en",
        timezone="UTC",
        is_active=True,
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token = create_access_token(user.id)

    response = await api_client.post(
        "/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "user_id": str(user.id),
            "text": "Hello Atlas",
            "conversation_id": None,
            "metadata": {},
        },
    )

    assert response.status_code == 200
