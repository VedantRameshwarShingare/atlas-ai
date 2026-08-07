"""Bootstrap middleware registration point."""

from __future__ import annotations

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint


class BootstrapMiddleware(BaseHTTPMiddleware):
    """Pass requests through while reserving a single middleware extension point."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Forward the request without applying application behavior."""
        return await call_next(request)


def add_api_middleware(app: FastAPI) -> None:
    """Register the bootstrap middleware placeholder on the FastAPI application."""
    app.add_middleware(BootstrapMiddleware)
