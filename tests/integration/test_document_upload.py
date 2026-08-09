"""Workspace document upload integration coverage."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest
from fastapi import status
from httpx import AsyncClient
from pydantic import SecretStr
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.documents import get_rag_engine
from app.core.config import settings


class FakeRAGEngine:
    """Deterministic RAG engine test double for document lifecycle tests."""

    def __init__(self) -> None:
        self.ingested_document_ids: list[str] = []
        self.deleted_document_ids: list[str] = []
        self.fail_ingest: bool = False

    async def ingest(self, *, file_path: str, document_id: str | None = None, metadata: dict | None = None) -> dict:
        del metadata
        if self.fail_ingest:
            raise RuntimeError("ingest failure")
        self.ingested_document_ids.append(document_id or "")
        return {"document_id": document_id, "chunks": 1, "stored": True, "file_path": file_path}

    async def delete(self, *, document_id: str) -> bool:
        self.deleted_document_ids.append(document_id)
        return True


@pytest.fixture(autouse=True)
def configure_auth_settings() -> None:
    """Use deterministic JWT settings for document tests."""
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
async def ensure_workspace_document_schema_compatibility(db_session: AsyncSession) -> None:
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

    await db_session.execute(text("ALTER TABLE documents ADD COLUMN IF NOT EXISTS workspace_id UUID"))
    await db_session.execute(text("ALTER TABLE documents ADD COLUMN IF NOT EXISTS uploaded_by UUID"))
    await db_session.execute(text("ALTER TABLE documents ADD COLUMN IF NOT EXISTS storage_path VARCHAR(500)"))
    await db_session.execute(text("ALTER TABLE documents ADD COLUMN IF NOT EXISTS content_type VARCHAR(255)"))
    await db_session.execute(text("ALTER TABLE documents ADD COLUMN IF NOT EXISTS file_size BIGINT"))
    await db_session.execute(text("ALTER TABLE documents ADD COLUMN IF NOT EXISTS error_message TEXT"))

    await db_session.execute(
        text(
            """
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_name = 'documents' AND column_name = 'user_id'
                ) THEN
                    ALTER TABLE documents ALTER COLUMN user_id DROP NOT NULL;
                END IF;

                IF EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_name = 'documents' AND column_name = 'document_type'
                ) THEN
                    ALTER TABLE documents ALTER COLUMN document_type DROP NOT NULL;
                    ALTER TABLE documents ALTER COLUMN document_type SET DEFAULT 'txt';
                END IF;

                IF EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_name = 'documents' AND column_name = 'file_path'
                ) THEN
                    ALTER TABLE documents ALTER COLUMN file_path DROP NOT NULL;
                    ALTER TABLE documents ALTER COLUMN file_path SET DEFAULT '';
                END IF;
            END
            $$;
            """
        )
    )

    await db_session.execute(text("UPDATE documents SET uploaded_by = user_id WHERE uploaded_by IS NULL"))
    await db_session.execute(text("UPDATE documents SET storage_path = file_path WHERE storage_path IS NULL"))
    await db_session.execute(
        text(
            "UPDATE documents "
            "SET content_type = COALESCE(document_type, 'application/octet-stream') "
            "WHERE content_type IS NULL"
        )
    )
    await db_session.execute(text("UPDATE documents SET file_size = 0 WHERE file_size IS NULL"))
    await db_session.execute(
        text("UPDATE documents SET status = 'ready' WHERE status NOT IN ('pending', 'processing', 'ready', 'failed')")
    )

    await db_session.execute(
        text(
            """
            UPDATE documents d
            SET workspace_id = m.workspace_id
            FROM memberships m
            WHERE d.workspace_id IS NULL AND m.user_id = d.uploaded_by
            """
        )
    )

    await db_session.commit()


@pytest.fixture
def fake_rag_engine() -> FakeRAGEngine:
    """Provide a mutable fake RAG engine for assertions."""
    return FakeRAGEngine()


@pytest.fixture(autouse=True)
def override_rag_engine(fake_rag_engine: FakeRAGEngine) -> None:
    """Override RAG engine dependency with a deterministic test double."""
    from app.main import app

    app.dependency_overrides[get_rag_engine] = lambda: fake_rag_engine
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_rag_engine, None)


@pytest.fixture(autouse=True)
def configure_document_settings(tmp_path: Path) -> None:
    """Store test uploads in a temporary folder with deterministic limits."""
    original_storage_directory = settings.documents.storage_directory
    original_max_size = settings.documents.max_upload_size_bytes
    original_extensions = list(settings.documents.allowed_extensions)
    original_content_types = list(settings.documents.allowed_content_types)

    settings.documents.storage_directory = str(tmp_path / "uploads")
    settings.documents.max_upload_size_bytes = 1024 * 1024
    settings.documents.allowed_extensions = [".pdf", ".txt", ".docx"]
    settings.documents.allowed_content_types = [
        "application/pdf",
        "text/plain",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ]

    try:
        yield
    finally:
        settings.documents.storage_directory = original_storage_directory
        settings.documents.max_upload_size_bytes = original_max_size
        settings.documents.allowed_extensions = original_extensions
        settings.documents.allowed_content_types = original_content_types


def _unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex}@example.com"


async def _register_and_login(client: AsyncClient, email: str, password: str = "SecurePass123") -> dict[str, str]:
    register = await client.post("/auth/register", json={"email": email, "password": password})
    assert register.status_code == status.HTTP_201_CREATED
    token = register.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_workspace_document_lifecycle_upload_list_get_delete(
    api_client: AsyncClient,
    fake_rag_engine: FakeRAGEngine,
) -> None:
    """Uploader can complete full document lifecycle in a workspace."""
    owner_headers = await _register_and_login(api_client, _unique_email("doc-owner"))

    workspace_response = await api_client.post(
        "/workspaces",
        headers=owner_headers,
        json={"name": "Docs Workspace"},
    )
    assert workspace_response.status_code == status.HTTP_201_CREATED
    workspace_id = workspace_response.json()["data"]["workspace"]["id"]

    upload_response = await api_client.post(
        f"/workspaces/{workspace_id}/documents",
        headers=owner_headers,
        files={"file": ("atlas.txt", b"Atlas AI retrieval content", "text/plain")},
    )
    assert upload_response.status_code == status.HTTP_201_CREATED

    uploaded_document = upload_response.json()["data"]["document"]
    document_id = uploaded_document["id"]
    assert uploaded_document["status"] == "ready"
    assert "storage_path" not in uploaded_document

    list_response = await api_client.get(f"/workspaces/{workspace_id}/documents", headers=owner_headers)
    assert list_response.status_code == status.HTTP_200_OK
    listed_document_ids = [item["id"] for item in list_response.json()["data"]["documents"]]
    assert document_id in listed_document_ids

    get_response = await api_client.get(f"/workspaces/{workspace_id}/documents/{document_id}", headers=owner_headers)
    assert get_response.status_code == status.HTTP_200_OK
    assert get_response.json()["data"]["document"]["id"] == document_id

    delete_response = await api_client.delete(
        f"/workspaces/{workspace_id}/documents/{document_id}", headers=owner_headers
    )
    assert delete_response.status_code == status.HTTP_200_OK

    deleted_get_response = await api_client.get(
        f"/workspaces/{workspace_id}/documents/{document_id}",
        headers=owner_headers,
    )
    assert deleted_get_response.status_code == status.HTTP_404_NOT_FOUND

    assert document_id in fake_rag_engine.ingested_document_ids
    assert document_id in fake_rag_engine.deleted_document_ids


@pytest.mark.asyncio
async def test_workspace_document_non_member_access_hidden(api_client: AsyncClient) -> None:
    """Non-members receive not-found semantics for workspace document routes."""
    owner_headers = await _register_and_login(api_client, _unique_email("doc-owner-access"))
    outsider_headers = await _register_and_login(api_client, _unique_email("doc-outsider"))

    workspace_response = await api_client.post("/workspaces", headers=owner_headers, json={"name": "Hidden Docs"})
    workspace_id = workspace_response.json()["data"]["workspace"]["id"]

    upload_response = await api_client.post(
        f"/workspaces/{workspace_id}/documents",
        headers=owner_headers,
        files={"file": ("atlas.txt", b"test", "text/plain")},
    )
    assert upload_response.status_code == status.HTTP_201_CREATED
    document_id = upload_response.json()["data"]["document"]["id"]

    outsider_list = await api_client.get(f"/workspaces/{workspace_id}/documents", headers=outsider_headers)
    outsider_get = await api_client.get(f"/workspaces/{workspace_id}/documents/{document_id}", headers=outsider_headers)
    outsider_upload = await api_client.post(
        f"/workspaces/{workspace_id}/documents",
        headers=outsider_headers,
        files={"file": ("atlas.txt", b"test", "text/plain")},
    )

    assert outsider_list.status_code == status.HTTP_404_NOT_FOUND
    assert outsider_get.status_code == status.HTTP_404_NOT_FOUND
    assert outsider_upload.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_workspace_document_delete_permissions(api_client: AsyncClient) -> None:
    """Only uploader, admin, or owner can delete workspace documents."""
    owner_email = _unique_email("doc-owner-delete")
    uploader_email = _unique_email("doc-uploader-delete")
    member_email = _unique_email("doc-member-delete")
    admin_email = _unique_email("doc-admin-delete")

    owner_headers = await _register_and_login(api_client, owner_email)
    uploader_headers = await _register_and_login(api_client, uploader_email)
    member_headers = await _register_and_login(api_client, member_email)
    admin_headers = await _register_and_login(api_client, admin_email)

    workspace_response = await api_client.post("/workspaces", headers=owner_headers, json={"name": "Doc Roles"})
    workspace_id = workspace_response.json()["data"]["workspace"]["id"]

    await api_client.post(
        f"/workspaces/{workspace_id}/members",
        headers=owner_headers,
        json={"email": uploader_email, "role": "member"},
    )
    await api_client.post(
        f"/workspaces/{workspace_id}/members",
        headers=owner_headers,
        json={"email": member_email, "role": "member"},
    )
    await api_client.post(
        f"/workspaces/{workspace_id}/members",
        headers=owner_headers,
        json={"email": admin_email, "role": "admin"},
    )

    upload_response = await api_client.post(
        f"/workspaces/{workspace_id}/documents",
        headers=uploader_headers,
        files={"file": ("atlas.txt", b"permission-test", "text/plain")},
    )
    assert upload_response.status_code == status.HTTP_201_CREATED
    document_id = upload_response.json()["data"]["document"]["id"]

    forbidden_delete = await api_client.delete(
        f"/workspaces/{workspace_id}/documents/{document_id}",
        headers=member_headers,
    )
    assert forbidden_delete.status_code == status.HTTP_403_FORBIDDEN

    admin_delete = await api_client.delete(
        f"/workspaces/{workspace_id}/documents/{document_id}",
        headers=admin_headers,
    )
    assert admin_delete.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_workspace_document_validation_and_failure_state(
    api_client: AsyncClient,
    fake_rag_engine: FakeRAGEngine,
) -> None:
    """Invalid uploads are rejected and ingestion failures persist failed metadata."""
    owner_headers = await _register_and_login(api_client, _unique_email("doc-owner-validate"))

    workspace_response = await api_client.post("/workspaces", headers=owner_headers, json={"name": "Doc Validate"})
    workspace_id = workspace_response.json()["data"]["workspace"]["id"]

    invalid_extension = await api_client.post(
        f"/workspaces/{workspace_id}/documents",
        headers=owner_headers,
        files={"file": ("atlas.exe", b"invalid", "application/octet-stream")},
    )
    assert invalid_extension.status_code == status.HTTP_400_BAD_REQUEST

    fake_rag_engine.fail_ingest = True
    failed_ingestion = await api_client.post(
        f"/workspaces/{workspace_id}/documents",
        headers=owner_headers,
        files={"file": ("atlas.txt", b"failure-case", "text/plain")},
    )
    assert failed_ingestion.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    documents_response = await api_client.get(f"/workspaces/{workspace_id}/documents", headers=owner_headers)
    assert documents_response.status_code == status.HTTP_200_OK
    documents = documents_response.json()["data"]["documents"]
    assert len(documents) == 1
    assert documents[0]["status"] == "failed"
    assert documents[0]["error_message"] == "Document ingestion failed"
