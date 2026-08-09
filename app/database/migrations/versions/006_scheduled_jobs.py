"""Add persistent scheduled jobs."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "006_scheduled_jobs"
down_revision = "005_finance_workspace_scoping"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the scheduled_jobs table."""
    op.create_table(
        "scheduled_jobs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "name",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "job_type",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "schedule",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "timezone",
            sa.String(length=100),
            nullable=False,
            server_default="UTC",
        ),
        sa.Column(
            "enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column(
            "payload",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'::json"),
        ),
        sa.Column(
            "last_run_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "next_run_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "last_error",
            sa.Text(),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_scheduled_jobs_user_id_users",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name="fk_scheduled_jobs_workspace_id_workspaces",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_scheduled_jobs_user_id"),
        "scheduled_jobs",
        ["user_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_scheduled_jobs_workspace_id"),
        "scheduled_jobs",
        ["workspace_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_scheduled_jobs_job_type"),
        "scheduled_jobs",
        ["job_type"],
        unique=False,
    )

    op.create_index(
        "ix_scheduled_jobs_user_enabled",
        "scheduled_jobs",
        ["user_id", "enabled"],
        unique=False,
    )

    op.create_index(
        "ix_scheduled_jobs_workspace_enabled",
        "scheduled_jobs",
        ["workspace_id", "enabled"],
        unique=False,
    )


def downgrade() -> None:
    """Drop the scheduled_jobs table."""
    op.drop_index(
        "ix_scheduled_jobs_workspace_enabled",
        table_name="scheduled_jobs",
    )

    op.drop_index(
        "ix_scheduled_jobs_user_enabled",
        table_name="scheduled_jobs",
    )

    op.drop_index(
        op.f("ix_scheduled_jobs_job_type"),
        table_name="scheduled_jobs",
    )

    op.drop_index(
        op.f("ix_scheduled_jobs_workspace_id"),
        table_name="scheduled_jobs",
    )

    op.drop_index(
        op.f("ix_scheduled_jobs_user_id"),
        table_name="scheduled_jobs",
    )

    op.drop_table("scheduled_jobs")
