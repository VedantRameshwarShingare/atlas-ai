"""Request-local correlation context for application logs."""

from __future__ import annotations

from contextvars import ContextVar, Token

_request_id: ContextVar[str] = ContextVar("atlas_request_id", default="-")


def get_request_id() -> str:
    """Return the request identifier associated with the current execution context."""
    return _request_id.get()


def set_request_id(request_id: str) -> Token[str]:
    """Attach a request identifier to the current execution context."""
    return _request_id.set(request_id)


def reset_request_id(token: Token[str]) -> None:
    """Restore the request context that was active before ``set_request_id``."""
    _request_id.reset(token)
