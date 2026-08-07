"""Alembic migration script template."""

from __future__ import annotations

revision = "${up_revision}"
down_revision = ${down_revision}
dependency_names = ${repr(depends_on)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade() -> None:
    """Apply migration."""
    ${imports if imports else ""}
    ${upgrades if upgrades else ""}


def downgrade() -> None:
    """Revert migration."""
    ${imports if imports else ""}
    ${downgrades if downgrades else ""}
