"""Add account credentials while preserving linked Telegram identities."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "002_authentication"
down_revision = "001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add nullable account fields safely before enforcing new account writes."""
    op.add_column("users", sa.Column("email", sa.String(length=320), nullable=True))
    op.add_column("users", sa.Column("password_hash", sa.String(length=255), nullable=True))
    op.alter_column("users", "telegram_user_id", existing_type=sa.String(length=64), nullable=True)
    op.create_index("ix_users_email", "users", ["email"], unique=True)


def downgrade() -> None:
    """Remove account fields without modifying existing Telegram identities."""
    op.drop_index("ix_users_email", table_name="users")
    op.drop_column("users", "password_hash")
    op.drop_column("users", "email")
    # Populate a deterministic fallback only for rows created while telegram_user_id was nullable.
    op.execute(
        sa.text(
            """
            UPDATE users
            SET telegram_user_id = CONCAT('legacy_', SUBSTRING(MD5(id::text), 1, 24))
            WHERE telegram_user_id IS NULL
            """
        )
    )
    op.alter_column("users", "telegram_user_id", existing_type=sa.String(length=64), nullable=False)
