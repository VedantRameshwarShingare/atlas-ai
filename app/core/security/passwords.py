"""Password hashing helpers using bcrypt."""

from __future__ import annotations

import bcrypt


def hash_password(password: str) -> str:
    """Return a bcrypt hash for a validated plaintext password."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Return whether a plaintext password matches its bcrypt hash."""
    if not password_hash:
        return False

    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (AttributeError, ValueError):
        return False
