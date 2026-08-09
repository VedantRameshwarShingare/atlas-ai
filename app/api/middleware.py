"""Bootstrap middleware registration point."""

from __future__ import annotations

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.logging.middleware import RequestIdMiddleware


class BootstrapMiddleware(BaseHTTPMiddleware):
    """Pass requests through while reserving a single middleware extension point."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Forward the request without applying application behavior."""
        return await call_next(request)


def add_api_middleware(app: FastAPI) -> None:
    """Register bootstrap and request-context middleware on the application."""
    app.add_middleware(BootstrapMiddleware)
    app.add_middleware(RequestIdMiddleware)
