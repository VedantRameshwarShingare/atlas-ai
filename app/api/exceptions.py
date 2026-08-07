"""Bootstrap exception-handler registration point."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette import status


def add_exception_handlers(app: FastAPI) -> None:
    """Register a minimal safe fallback for unexpected HTTP application errors."""

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_: Request, __: Exception) -> JSONResponse:
        """Return a stable response without exposing internal exception details."""
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal Server Error"},
        )
