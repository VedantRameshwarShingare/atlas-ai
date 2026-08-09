"""Scope watchlists and alerts to workspaces for finance capabilities."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "005_finance_workspace_scoping"
down_revision = "004_documents_workspace_rag"
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
            "description": "Auto-generated workspace for finance entities",
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


def _backfill_workspace_ids(bind: sa.engine.Connection, table_name: str) -> None:
    user_ids = (
        bind.execute(sa.text(f"SELECT DISTINCT user_id FROM {table_name} WHERE user_id IS NOT NULL")).scalars().all()
    )

    for user_id in user_ids:
        workspace_id = _choose_or_create_workspace(bind, user_id)
        bind.execute(
            sa.text(
                f"""
                UPDATE {table_name}
                SET workspace_id = :workspace_id
                WHERE user_id = :user_id AND workspace_id IS NULL
                """
            ),
            {"workspace_id": workspace_id, "user_id": user_id},
        )


def upgrade() -> None:
    """Add workspace ownership and thresholds for finance watchlist/alerts."""
    bind = op.get_bind()

    op.add_column("watchlists", sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=True))

    op.add_column("alerts", sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("alerts", sa.Column("threshold", sa.Float(), nullable=True))

    _backfill_workspace_ids(bind, "watchlists")
    _backfill_workspace_ids(bind, "alerts")

    bind.execute(sa.text("UPDATE alerts SET threshold = 0.0 WHERE threshold IS NULL"))

    op.alter_column("watchlists", "workspace_id", existing_type=postgresql.UUID(as_uuid=True), nullable=False)
    op.alter_column("alerts", "workspace_id", existing_type=postgresql.UUID(as_uuid=True), nullable=False)
    op.alter_column("alerts", "threshold", existing_type=sa.Float(), nullable=False)

    op.create_index(op.f("ix_watchlists_workspace_id"), "watchlists", ["workspace_id"], unique=False)
    op.create_index(op.f("ix_alerts_workspace_id"), "alerts", ["workspace_id"], unique=False)

    op.create_foreign_key(
        "fk_watchlists_workspace_id_workspaces",
        "watchlists",
        "workspaces",
        ["workspace_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_alerts_workspace_id_workspaces",
        "alerts",
        "workspaces",
        ["workspace_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint("uq_watchlists_user_symbol", "watchlists", type_="unique")
    op.create_unique_constraint("uq_watchlists_workspace_symbol", "watchlists", ["workspace_id", "symbol"])


def downgrade() -> None:
    """Revert workspace-scoped finance ownership fields."""
    op.drop_constraint("uq_watchlists_workspace_symbol", "watchlists", type_="unique")
    op.create_unique_constraint("uq_watchlists_user_symbol", "watchlists", ["user_id", "symbol"])

    op.drop_constraint("fk_alerts_workspace_id_workspaces", "alerts", type_="foreignkey")
    op.drop_constraint("fk_watchlists_workspace_id_workspaces", "watchlists", type_="foreignkey")

    op.drop_index(op.f("ix_alerts_workspace_id"), table_name="alerts")
    op.drop_index(op.f("ix_watchlists_workspace_id"), table_name="watchlists")

    op.drop_column("alerts", "threshold")
    op.drop_column("alerts", "workspace_id")
    op.drop_column("watchlists", "workspace_id")
