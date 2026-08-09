"""Add workspaces and memberships with role-based collaboration support."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "003_workspaces_memberships"
down_revision = "002_authentication"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create workspace and membership tables and workspace link on conversations."""
    op.create_table(
        "workspaces",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_workspaces_created_at"), "workspaces", ["created_at"], unique=False)
    op.create_index(op.f("ix_workspaces_updated_at"), "workspaces", ["updated_at"], unique=False)

    op.create_table(
        "memberships",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workspace_id", "user_id", name="uq_memberships_workspace_user"),
        sa.CheckConstraint("role IN ('owner', 'admin', 'member')", name="ck_memberships_role"),
    )
    op.create_index(op.f("ix_memberships_created_at"), "memberships", ["created_at"], unique=False)
    op.create_index(op.f("ix_memberships_updated_at"), "memberships", ["updated_at"], unique=False)
    op.create_index(op.f("ix_memberships_workspace_id"), "memberships", ["workspace_id"], unique=False)
    op.create_index(op.f("ix_memberships_user_id"), "memberships", ["user_id"], unique=False)

    op.add_column("conversations", sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index(op.f("ix_conversations_workspace_id"), "conversations", ["workspace_id"], unique=False)
    op.create_foreign_key(
        "fk_conversations_workspace_id_workspaces",
        "conversations",
        "workspaces",
        ["workspace_id"],
        ["id"],
    )


def downgrade() -> None:
    """Remove workspaces and memberships and drop conversation workspace link."""
    op.drop_constraint("fk_conversations_workspace_id_workspaces", "conversations", type_="foreignkey")
    op.drop_index(op.f("ix_conversations_workspace_id"), table_name="conversations")
    op.drop_column("conversations", "workspace_id")

    op.drop_index(op.f("ix_memberships_user_id"), table_name="memberships")
    op.drop_index(op.f("ix_memberships_workspace_id"), table_name="memberships")
    op.drop_index(op.f("ix_memberships_updated_at"), table_name="memberships")
    op.drop_index(op.f("ix_memberships_created_at"), table_name="memberships")
    op.drop_table("memberships")

    op.drop_index(op.f("ix_workspaces_updated_at"), table_name="workspaces")
    op.drop_index(op.f("ix_workspaces_created_at"), table_name="workspaces")
    op.drop_table("workspaces")
