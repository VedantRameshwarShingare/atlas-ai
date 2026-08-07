"""Minimal FastAPI application bootstrap for Atlas AI."""

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from app.api.exceptions import add_exception_handlers
from app.api.middleware import add_api_middleware
from app.api.router import api_router
from app.core.config import settings
from app.core.lifespan import lifespan


class RootResponse(BaseModel):
    """Public application-status response returned by the root endpoint."""

    name: str
    status: str
    version: str


app = FastAPI(
    title=settings.application.name,
    version=settings.application.version,
    description="Atlas AI HTTP API.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)
app.include_router(api_router)
add_api_middleware(app)
add_exception_handlers(app)


@app.get("/", response_model=RootResponse, tags=["application"])
async def root() -> RootResponse:
    """Return the minimal public application status."""
    return RootResponse(
        name=settings.application.name,
        status="running",
        version=settings.application.version,
    )


__all__ = ["app"]
