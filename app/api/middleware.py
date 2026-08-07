"""Middleware for the FastAPI interface layer."""

from __future__ import annotations

import time
from typing import Callable

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware


def add_api_middleware(app: FastAPI) -> None:
    """Register request logging, tracing, compression, CORS, and trusted host middleware."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    @app.middleware("http")
    async def request_logging_middleware(request: Request, call_next: Callable) -> object:
        started_at = time.perf_counter()
        request_id = request.headers.get("X-Request-ID") or "req-unknown"
        request.state.request_id = request_id
        response = await call_next(request)
        elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-ms"] = str(elapsed_ms)
        return response
