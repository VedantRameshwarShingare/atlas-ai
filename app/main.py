"""Application entrypoint for Atlas AI."""

from __future__ import annotations

from fastapi import FastAPI

from app.api.exceptions import add_exception_handlers
from app.api.middleware import add_api_middleware
from app.api.router import api_router

app = FastAPI(title="Atlas AI", version="0.1.0")
app.include_router(api_router, prefix="/api")
add_api_middleware(app)
add_exception_handlers(app)

__all__ = ["app"]
