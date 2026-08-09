"""Workspace and membership integration coverage."""

from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import AsyncClient
from pydantic import SecretStr
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings


def _unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex}@example.com"


@pytest.fixture(autouse=True)
def configure_auth_settings() -> None:
    """Use deterministic JWT settings for workspace tests."""
    original_secret = settings.auth.jwt_secret_key
    original_algorithm = settings.auth.jwt_algorithm
    original_expire_minutes = settings.auth.access_token_expire_minutes

    settings.auth.jwt_secret_key = SecretStr("workspace-test-jwt-secret-key-32-bytes")
    settings.auth.jwt_algorithm = "HS256"
    settings.auth.access_token_expire_minutes = 60
    try:
        yield
    finally:
        settings.auth.jwt_secret_key = original_secret
        settings.auth.jwt_algorithm = original_algorithm
        settings.auth.access_token_expire_minutes = original_expire_minutes


@pytest.fixture(autouse=True)
async def ensure_workspace_schema_compatibility(db_session: AsyncSession) -> None:
    """Support local test DBs that have not applied the latest migration head."""
    await db_session.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(320)"))
    await db_session.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255)"))
    await db_session.execute(text("ALTER TABLE users ALTER COLUMN telegram_user_id DROP NOT NULL"))
    await db_session.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email)"))

    await db_session.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS workspaces (
                id UUID PRIMARY KEY,
                created_at TIMESTAMPTZ NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL,
                name VARCHAR(255) NOT NULL,
                description VARCHAR(1000)
            )
            """
        )
    )
    await db_session.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS memberships (
                id UUID PRIMARY KEY,
                created_at TIMESTAMPTZ NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL,
                workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
                user_id UUID NOT NULL REFERENCES users(id),
                role VARCHAR(20) NOT NULL CHECK (role IN ('owner', 'admin', 'member')),
                CONSTRAINT uq_memberships_workspace_user UNIQUE (workspace_id, user_id)
            )
            """
        )
    )
    await db_session.execute(text("CREATE INDEX IF NOT EXISTS ix_workspaces_created_at ON workspaces (created_at)"))
    await db_session.execute(text("CREATE INDEX IF NOT EXISTS ix_workspaces_updated_at ON workspaces (updated_at)"))
    await db_session.execute(text("CREATE INDEX IF NOT EXISTS ix_memberships_created_at ON memberships (created_at)"))
    await db_session.execute(text("CREATE INDEX IF NOT EXISTS ix_memberships_updated_at ON memberships (updated_at)"))
    await db_session.execute(
        text("CREATE INDEX IF NOT EXISTS ix_memberships_workspace_id ON memberships (workspace_id)")
    )
    await db_session.execute(text("CREATE INDEX IF NOT EXISTS ix_memberships_user_id ON memberships (user_id)"))
    await db_session.execute(text("ALTER TABLE conversations ADD COLUMN IF NOT EXISTS workspace_id UUID"))
    await db_session.execute(
        text("CREATE INDEX IF NOT EXISTS ix_conversations_workspace_id ON conversations (workspace_id)")
    )
    await db_session.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS watchlists (
                id UUID PRIMARY KEY,
                created_at TIMESTAMPTZ NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL,
                workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
                user_id UUID NOT NULL REFERENCES users(id),
                symbol VARCHAR(20) NOT NULL,
                company_name VARCHAR(255),
                market VARCHAR(50),
                is_active BOOLEAN NOT NULL
            )
            """
        )
    )
    await db_session.execute(text("ALTER TABLE watchlists ADD COLUMN IF NOT EXISTS workspace_id UUID"))
    await db_session.execute(text("ALTER TABLE watchlists ADD COLUMN IF NOT EXISTS company_name VARCHAR(255)"))
    await db_session.execute(text("ALTER TABLE watchlists ADD COLUMN IF NOT EXISTS market VARCHAR(50)"))
    await db_session.execute(text("ALTER TABLE watchlists ADD COLUMN IF NOT EXISTS is_active BOOLEAN"))

    await db_session.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS alerts (
                id UUID PRIMARY KEY,
                created_at TIMESTAMPTZ NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL,
                workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
                user_id UUID NOT NULL REFERENCES users(id),
                alert_type VARCHAR(50) NOT NULL,
                symbol VARCHAR(20) NOT NULL,
                condition VARCHAR(255) NOT NULL,
                threshold DOUBLE PRECISION NOT NULL,
                is_enabled BOOLEAN NOT NULL,
                last_triggered TIMESTAMPTZ
            )
            """
        )
    )
    await db_session.execute(text("ALTER TABLE alerts ADD COLUMN IF NOT EXISTS workspace_id UUID"))
    await db_session.execute(text("ALTER TABLE alerts ADD COLUMN IF NOT EXISTS threshold DOUBLE PRECISION"))
    await db_session.execute(text("ALTER TABLE alerts ADD COLUMN IF NOT EXISTS is_enabled BOOLEAN"))
    await db_session.execute(text("UPDATE alerts SET threshold = 0.0 WHERE threshold IS NULL"))
    await db_session.commit()


async def _register_and_login(client: AsyncClient, email: str, password: str = "SecurePass123") -> dict[str, str]:
    """Register a unique user and return bearer auth headers."""
    register = await client.post("/auth/register", json={"email": email, "password": password})
    assert register.status_code == 201
    token = register.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_workspace_create_list_and_member_isolation(api_client: AsyncClient) -> None:
    """Members only see workspaces they belong to."""
    owner_headers = await _register_and_login(api_client, _unique_email("ws-owner"))
    other_headers = await _register_and_login(api_client, _unique_email("ws-other"))

    created = await api_client.post(
        "/workspaces",
        headers=owner_headers,
        json={"name": "Owner Workspace", "description": "Primary workspace"},
    )
    assert created.status_code == 201
    workspace_id = created.json()["data"]["workspace"]["id"]

    owner_list = await api_client.get("/workspaces", headers=owner_headers)
    other_list = await api_client.get("/workspaces", headers=other_headers)

    assert owner_list.status_code == 200
    assert other_list.status_code == 200
    assert any(item["id"] == workspace_id for item in owner_list.json()["data"]["workspaces"])
    assert all(item["id"] != workspace_id for item in other_list.json()["data"]["workspaces"])


@pytest.mark.asyncio
async def test_workspace_membership_role_permissions(api_client: AsyncClient) -> None:
    """Owner/admin/member permissions are enforced for membership writes."""
    owner_email = _unique_email("role-owner")
    admin_email = _unique_email("role-admin")
    member_email = _unique_email("role-member")
    outsider_email = _unique_email("role-outsider")

    owner_headers = await _register_and_login(api_client, owner_email)
    admin_headers = await _register_and_login(api_client, admin_email)
    member_headers = await _register_and_login(api_client, member_email)
    await _register_and_login(api_client, outsider_email)

    workspace_response = await api_client.post("/workspaces", headers=owner_headers, json={"name": "Role WS"})
    workspace_id = workspace_response.json()["data"]["workspace"]["id"]

    add_admin = await api_client.post(
        f"/workspaces/{workspace_id}/members",
        headers=owner_headers,
        json={"email": admin_email, "role": "admin"},
    )
    assert add_admin.status_code == 201

    add_member_by_admin = await api_client.post(
        f"/workspaces/{workspace_id}/members",
        headers=admin_headers,
        json={"email": member_email, "role": "member"},
    )
    assert add_member_by_admin.status_code == 201

    admin_promote_to_admin = await api_client.post(
        f"/workspaces/{workspace_id}/members",
        headers=admin_headers,
        json={"email": outsider_email, "role": "admin"},
    )
    member_add_attempt = await api_client.post(
        f"/workspaces/{workspace_id}/members",
        headers=member_headers,
        json={"email": outsider_email, "role": "member"},
    )

    assert admin_promote_to_admin.status_code == 403
    assert member_add_attempt.status_code == 403


@pytest.mark.asyncio
async def test_workspace_owner_safety_and_delete_rules(api_client: AsyncClient) -> None:
    """Workspace keeps at least one owner and only owners can delete."""
    owner_email = _unique_email("safe-owner")
    second_owner_email = _unique_email("safe-owner2")
    admin_email = _unique_email("safe-admin")

    owner_headers = await _register_and_login(api_client, owner_email)
    await _register_and_login(api_client, second_owner_email)
    admin_headers = await _register_and_login(api_client, admin_email)

    workspace_response = await api_client.post("/workspaces", headers=owner_headers, json={"name": "Safety WS"})
    assert workspace_response.status_code == 201
    workspace_id = workspace_response.json()["data"]["workspace"]["id"]

    add_second_owner = await api_client.post(
        f"/workspaces/{workspace_id}/members",
        headers=owner_headers,
        json={"email": second_owner_email, "role": "owner"},
    )
    add_admin = await api_client.post(
        f"/workspaces/{workspace_id}/members",
        headers=owner_headers,
        json={"email": admin_email, "role": "admin"},
    )
    assert add_second_owner.status_code == 201
    assert add_admin.status_code == 201

    second_owner_id = add_second_owner.json()["data"]["membership"]["user_id"]
    owner_me = await api_client.get("/auth/me", headers=owner_headers)
    owner_id = owner_me.json()["id"]

    remove_second_owner = await api_client.delete(
        f"/workspaces/{workspace_id}/members/{second_owner_id}",
        headers=owner_headers,
    )
    remove_last_owner_self = await api_client.delete(
        f"/workspaces/{workspace_id}/members/{owner_id}",
        headers=owner_headers,
    )
    admin_delete_workspace = await api_client.delete(f"/workspaces/{workspace_id}", headers=admin_headers)
    owner_delete_workspace = await api_client.delete(f"/workspaces/{workspace_id}", headers=owner_headers)

    assert remove_second_owner.status_code == 200
    assert remove_last_owner_self.status_code == 400
    assert admin_delete_workspace.status_code == 403
    assert owner_delete_workspace.status_code == 200


@pytest.mark.asyncio
async def test_workspace_non_member_access_is_hidden(api_client: AsyncClient) -> None:
    """Non-members receive not-found semantics for workspace resources."""
    owner_email = _unique_email("access-owner")
    outsider_email = _unique_email("access-outsider")

    owner_headers = await _register_and_login(api_client, owner_email)
    outsider_headers = await _register_and_login(api_client, outsider_email)

    created = await api_client.post("/workspaces", headers=owner_headers, json={"name": "Access WS"})
    workspace_id = created.json()["data"]["workspace"]["id"]

    outsider_get = await api_client.get(f"/workspaces/{workspace_id}", headers=outsider_headers)
    outsider_members = await api_client.get(f"/workspaces/{workspace_id}/members", headers=outsider_headers)

    assert outsider_get.status_code == 404
    assert outsider_members.status_code == 404
