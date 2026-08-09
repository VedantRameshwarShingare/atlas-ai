"""Align documents schema with workspace-scoped upload and RAG lifecycle."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "004_documents_workspace_rag"
down_revision = "003_workspaces_memberships"
branch_labels = None
depends_on = None


def _choose_or_create_workspace(bind: sa.engine.Connection, user_id: UUID) -> UUID:
    existing_workspace_id = bind.execute(
        sa.text(
            """
            SELECT m.workspace_id
            FROM memberships m
            WHERE m.user_id = :user_id
            ORDER BY m.created_at ASC
            LIMIT 1
            """
        ),
        {"user_id": user_id},
    ).scalar_one_or_none()

    if existing_workspace_id is not None:
        return existing_workspace_id

    now = datetime.now(UTC)
    workspace_id = uuid4()
    membership_id = uuid4()

    bind.execute(
        sa.text(
            """
            INSERT INTO workspaces (id, created_at, updated_at, name, description)
            VALUES (:id, :created_at, :updated_at, :name, :description)
            """
        ),
        {
            "id": workspace_id,
            "created_at": now,
            "updated_at": now,
            "name": f"Personal Workspace {str(user_id)[:8]}",
            "description": "Auto-generated workspace for existing documents",
        },
    )

    bind.execute(
        sa.text(
            """
            INSERT INTO memberships (id, created_at, updated_at, workspace_id, user_id, role)
            VALUES (:id, :created_at, :updated_at, :workspace_id, :user_id, :role)
            """
        ),
        {
            "id": membership_id,
            "created_at": now,
            "updated_at": now,
            "workspace_id": workspace_id,
            "user_id": user_id,
            "role": "owner",
        },
    )

    return workspace_id


def upgrade() -> None:
    """Alter documents table to workspace-aware storage and lifecycle metadata."""
    bind = op.get_bind()

    op.alter_column(
        "documents",
        "user_id",
        new_column_name="uploaded_by",
        existing_type=postgresql.UUID(as_uuid=True),
        existing_nullable=False,
    )

    op.alter_column(
        "documents",
        "file_path",
        new_column_name="storage_path",
        existing_type=sa.String(length=500),
        existing_nullable=False,
    )

    op.add_column("documents", sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("documents", sa.Column("content_type", sa.String(length=255), nullable=True))
    op.add_column("documents", sa.Column("file_size", sa.BigInteger(), nullable=True))
    op.add_column("documents", sa.Column("error_message", sa.Text(), nullable=True))

    bind.execute(sa.text("UPDATE documents SET content_type = COALESCE(document_type, 'application/octet-stream')"))
    bind.execute(sa.text("UPDATE documents SET file_size = 0 WHERE file_size IS NULL"))
    bind.execute(
        sa.text(
            "UPDATE documents SET status = 'ready' WHERE status NOT IN ('pending', 'processing', 'ready', 'failed')"
        )
    )

    user_ids = (
        bind.execute(sa.text("SELECT DISTINCT uploaded_by FROM documents WHERE uploaded_by IS NOT NULL"))
        .scalars()
        .all()
    )

    for user_id in user_ids:
        workspace_id = _choose_or_create_workspace(bind, user_id)
        bind.execute(
            sa.text(
                """
                UPDATE documents
                SET workspace_id = :workspace_id
                WHERE uploaded_by = :user_id AND workspace_id IS NULL
                """
            ),
            {"workspace_id": workspace_id, "user_id": user_id},
        )

    op.alter_column("documents", "workspace_id", existing_type=postgresql.UUID(as_uuid=True), nullable=False)
    op.alter_column("documents", "content_type", existing_type=sa.String(length=255), nullable=False)
    op.alter_column("documents", "file_size", existing_type=sa.BigInteger(), nullable=False)

    op.drop_index(op.f("ix_documents_user_id"), table_name="documents")
    op.create_index(op.f("ix_documents_workspace_id"), "documents", ["workspace_id"], unique=False)
    op.create_index(op.f("ix_documents_uploaded_by"), "documents", ["uploaded_by"], unique=False)

    op.drop_column("documents", "document_type")
    op.drop_column("documents", "summary")

    op.create_foreign_key(
        "fk_documents_workspace_id_workspaces",
        "documents",
        "workspaces",
        ["workspace_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    """Restore the legacy documents columns and ownership model."""
    op.drop_constraint("fk_documents_workspace_id_workspaces", "documents", type_="foreignkey")

    op.add_column("documents", sa.Column("summary", sa.Text(), nullable=True))
    op.add_column(
        "documents", sa.Column("document_type", sa.String(length=50), nullable=False, server_default="unknown")
    )

    op.execute(
        sa.text(
            """
            UPDATE documents
            SET document_type = CASE
                WHEN content_type = 'application/pdf' THEN 'pdf'
                WHEN content_type = 'text/plain' THEN 'txt'
                WHEN content_type =
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document' THEN 'docx'
                ELSE 'unknown'
            END
            """
        )
    )

    op.alter_column(
        "documents",
        "storage_path",
        new_column_name="file_path",
        existing_type=sa.String(length=500),
        existing_nullable=False,
    )

    op.alter_column(
        "documents",
        "uploaded_by",
        new_column_name="user_id",
        existing_type=postgresql.UUID(as_uuid=True),
        existing_nullable=False,
    )

    op.drop_index(op.f("ix_documents_uploaded_by"), table_name="documents")
    op.drop_index(op.f("ix_documents_workspace_id"), table_name="documents")
    op.create_index(op.f("ix_documents_user_id"), "documents", ["user_id"], unique=False)

    op.drop_column("documents", "error_message")
    op.drop_column("documents", "file_size")
    op.drop_column("documents", "content_type")
    op.drop_column("documents", "workspace_id")

    op.alter_column("documents", "document_type", server_default=None)
