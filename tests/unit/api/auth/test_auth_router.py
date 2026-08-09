"""Authentication endpoint and dependency coverage."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest
from httpx import AsyncClient
from pydantic import SecretStr
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security.passwords import hash_password, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository


async def _column_exists(session: AsyncSession, column_name: str) -> bool:
    """Return whether the users table has the requested column."""
    query = text(
        """
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = :column_name
        """
    )
    result = await session.execute(query, {"column_name": column_name})
    return result.scalar_one_or_none() is not None


def _unique_email(prefix: str) -> str:
    """Return a deterministic-format unique email to avoid cross-run collisions."""
    return f"{prefix}-{uuid4().hex}@example.com"


@pytest.fixture(autouse=True)
def configure_auth_settings() -> None:
    """Use deterministic JWT settings for auth tests."""
    original_secret = settings.auth.jwt_secret_key
    original_algorithm = settings.auth.jwt_algorithm
    original_expire_minutes = settings.auth.access_token_expire_minutes

    settings.auth.jwt_secret_key = SecretStr("unit-test-jwt-secret-key-32-bytes")
    settings.auth.jwt_algorithm = "HS256"
    settings.auth.access_token_expire_minutes = 60
    try:
        yield
    finally:
        settings.auth.jwt_secret_key = original_secret
        settings.auth.jwt_algorithm = original_algorithm
        settings.auth.access_token_expire_minutes = original_expire_minutes


@pytest.fixture(autouse=True)
async def ensure_auth_schema_compatibility(db_session: AsyncSession) -> None:
    """Ensure auth columns exist in test databases that have only the initial schema."""
    if not await _column_exists(db_session, "email"):
        await db_session.execute(text("ALTER TABLE users ADD COLUMN email VARCHAR(320)"))

    if not await _column_exists(db_session, "password_hash"):
        await db_session.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255)"))

    await db_session.execute(text("ALTER TABLE users ALTER COLUMN telegram_user_id DROP NOT NULL"))
    await db_session.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email)"))
    await db_session.commit()


async def _create_user(
    session: AsyncSession,
    *,
    email: str,
    password: str,
    is_active: bool = True,
    telegram_user_id: str | None = None,
) -> User:
    """Persist a user for authentication tests."""
    user = User(
        email=email.lower(),
        password_hash=hash_password(password),
        telegram_user_id=telegram_user_id,
        language="en",
        timezone="UTC",
        is_active=is_active,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


def _expired_access_token(user_id: str) -> str:
    """Create an already-expired access token for failure-path tests."""
    now = datetime.now(UTC)
    payload = {
        "sub": user_id,
        "type": "access",
        "iat": now - timedelta(minutes=10),
        "exp": now - timedelta(minutes=1),
    }
    return jwt.encode(
        payload,
        settings.auth.jwt_secret_key.get_secret_value(),
        algorithm=settings.auth.jwt_algorithm,
    )


@pytest.mark.asyncio
async def test_register_success_normalizes_email_and_hashes_password(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Registration returns a token and stores normalized credentials securely."""
    local_part = f"user-{uuid4().hex}"
    mixed_case_email = f"{local_part}@Example.COM"
    normalized_email = f"{local_part}@example.com"

    response = await api_client.post(
        "/auth/register",
        json={"email": mixed_case_email, "password": "SecurePass123"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"
    assert "password" not in body
    assert "password_hash" not in body

    user = await UserRepository(db_session).get_by_email(normalized_email)
    assert user is not None
    assert user.email == normalized_email
    assert user.password_hash != "SecurePass123"
    assert verify_password("SecurePass123", user.password_hash or "") is True


@pytest.mark.asyncio
async def test_register_duplicate_email_rejected(api_client: AsyncClient, db_session: AsyncSession) -> None:
    """Registration must reject duplicate emails after normalization."""
    duplicate_email = _unique_email("duplicate")
    await _create_user(db_session, email=duplicate_email, password="SecurePass123")

    response = await api_client.post(
        "/auth/register",
        json={"email": duplicate_email.upper(), "password": "AnotherPass123"},
    )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_register_invalid_email_rejected(api_client: AsyncClient) -> None:
    """Registration must reject invalid email values."""
    response = await api_client.post(
        "/auth/register",
        json={"email": "not-an-email", "password": "SecurePass123"},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_blank_and_short_password_rejected(api_client: AsyncClient) -> None:
    """Registration must reject blank and too-short passwords."""
    blank_email = _unique_email("blank")
    short_email = _unique_email("short")

    blank = await api_client.post(
        "/auth/register",
        json={"email": blank_email, "password": "    "},
    )
    short = await api_client.post(
        "/auth/register",
        json={"email": short_email, "password": "short"},
    )

    assert blank.status_code == 422
    assert short.status_code == 422


@pytest.mark.asyncio
async def test_login_success_returns_jwt_that_authenticates(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Valid login returns a bearer token that can call /auth/me."""
    email = _unique_email("login")
    user = await _create_user(db_session, email=email, password="SecurePass123")

    login = await api_client.post(
        "/auth/login",
        json={"email": email.upper(), "password": "SecurePass123"},
    )
    assert login.status_code == 200

    token = login.json()["access_token"]
    me = await api_client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert me.status_code == 200
    body = me.json()
    assert body["id"] == str(user.id)
    assert body["email"] == email
    assert "password_hash" not in body


@pytest.mark.asyncio
async def test_login_wrong_password_and_unknown_email_share_auth_error(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Auth failures should not reveal whether an email exists."""
    known_email = _unique_email("known")
    unknown_email = _unique_email("unknown")
    await _create_user(db_session, email=known_email, password="SecurePass123")

    wrong_password = await api_client.post(
        "/auth/login",
        json={"email": known_email, "password": "WrongPassword123"},
    )
    unknown_email_response = await api_client.post(
        "/auth/login",
        json={"email": unknown_email, "password": "SecurePass123"},
    )

    assert wrong_password.status_code == 401
    assert unknown_email_response.status_code == 401
    assert wrong_password.json() == unknown_email_response.json()


@pytest.mark.asyncio
async def test_login_rejects_inactive_user(api_client: AsyncClient, db_session: AsyncSession) -> None:
    """Inactive users must not obtain JWTs."""
    email = _unique_email("inactive")
    await _create_user(db_session, email=email, password="SecurePass123", is_active=False)

    response = await api_client.post(
        "/auth/login",
        json={"email": email, "password": "SecurePass123"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_rejects_missing_malformed_invalid_signature_and_expired_tokens(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """/auth/me must reject invalid authentication forms and tokens."""
    user = await _create_user(db_session, email=_unique_email("jwt"), password="SecurePass123")

    missing = await api_client.get("/auth/me")
    malformed = await api_client.get("/auth/me", headers={"Authorization": "Bearer not.a.jwt"})
    invalid_bearer = await api_client.get("/auth/me", headers={"Authorization": "Token abc"})

    wrong_secret_token = jwt.encode(
        {
            "sub": str(user.id),
            "type": "access",
            "iat": datetime.now(UTC),
            "exp": datetime.now(UTC) + timedelta(minutes=10),
        },
        "different-secret-key-32-bytes-long",
        algorithm=settings.auth.jwt_algorithm,
    )
    invalid_signature = await api_client.get("/auth/me", headers={"Authorization": f"Bearer {wrong_secret_token}"})

    expired = await api_client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {_expired_access_token(str(user.id))}"},
    )

    assert missing.status_code == 401
    assert malformed.status_code == 401
    assert invalid_bearer.status_code == 401
    assert invalid_signature.status_code == 401
    assert expired.status_code == 401


@pytest.mark.asyncio
async def test_me_rejects_nonexistent_and_inactive_users(api_client: AsyncClient, db_session: AsyncSession) -> None:
    """/auth/me must reject tokens for missing users and inactive accounts."""
    missing_user_token = jwt.encode(
        {
            "sub": str(uuid4()),
            "type": "access",
            "iat": datetime.now(UTC),
            "exp": datetime.now(UTC) + timedelta(minutes=10),
        },
        settings.auth.jwt_secret_key.get_secret_value(),
        algorithm=settings.auth.jwt_algorithm,
    )

    inactive_user = await _create_user(
        db_session,
        email=_unique_email("inactive-me"),
        password="SecurePass123",
        is_active=False,
    )
    inactive_token = jwt.encode(
        {
            "sub": str(inactive_user.id),
            "type": "access",
            "iat": datetime.now(UTC),
            "exp": datetime.now(UTC) + timedelta(minutes=10),
        },
        settings.auth.jwt_secret_key.get_secret_value(),
        algorithm=settings.auth.jwt_algorithm,
    )

    missing_user = await api_client.get("/auth/me", headers={"Authorization": f"Bearer {missing_user_token}"})
    inactive = await api_client.get("/auth/me", headers={"Authorization": f"Bearer {inactive_token}"})

    assert missing_user.status_code == 401
    assert inactive.status_code == 403


@pytest.mark.asyncio
async def test_telegram_identity_compatibility_nullable_and_preserved(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Telegram-linked and email-password users coexist without identity loss."""
    nullable_email = _unique_email("nullable-telegram")
    register = await api_client.post(
        "/auth/register",
        json={"email": nullable_email, "password": "SecurePass123"},
    )
    assert register.status_code == 201

    nullable_user = await UserRepository(db_session).get_by_email(nullable_email)
    assert nullable_user is not None
    assert nullable_user.telegram_user_id is None

    telegram_email = _unique_email("telegram-linked")
    telegram_user = await _create_user(
        db_session,
        email=telegram_email,
        password="SecurePass123",
        telegram_user_id=f"tg_{uuid4().hex[:16]}",
    )
    original_telegram_id = telegram_user.telegram_user_id

    login = await api_client.post(
        "/auth/login",
        json={"email": telegram_email, "password": "SecurePass123"},
    )
    token = login.json()["access_token"]
    me = await api_client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert login.status_code == 200
    assert me.status_code == 200
    assert me.json()["telegram_user_id"] == original_telegram_id


@pytest.mark.asyncio
async def test_authenticated_endpoint_and_ownership_authorization(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Authenticated chat works and cross-user conversation access is blocked."""
    owner_email = _unique_email("owner")
    other_email = _unique_email("other")
    owner = await _create_user(db_session, email=owner_email, password="SecurePass123")
    other = await _create_user(db_session, email=other_email, password="SecurePass123")

    owner_login = await api_client.post(
        "/auth/login",
        json={"email": owner_email, "password": "SecurePass123"},
    )
    other_login = await api_client.post(
        "/auth/login",
        json={"email": other_email, "password": "SecurePass123"},
    )

    owner_headers = {"Authorization": f"Bearer {owner_login.json()['access_token']}"}
    other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}

    unauthenticated = await api_client.post("/chat", json={"text": "Hello"})
    authenticated = await api_client.post("/chat", headers=owner_headers, json={"text": "Owner chat"})
    conversation_id = authenticated.json()["data"]["conversation_id"]
    forbidden_read = await api_client.get(f"/conversations/{conversation_id}", headers=other_headers)

    assert owner.id != other.id
    assert unauthenticated.status_code == 401
    assert authenticated.status_code == 200
    assert forbidden_read.status_code == 404
