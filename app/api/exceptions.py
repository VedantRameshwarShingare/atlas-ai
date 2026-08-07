"""Global exception handling for the FastAPI layer."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette import status

from app.api.responses import APIErrorResponse, APIResponse


def add_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers for validation and runtime failures."""

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=APIErrorResponse(
                error="validation_error",
                message="Request validation failed.",
                details=exc.errors(),
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def unexpected_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=APIErrorResponse(
                error="internal_server_error",
                message="An unexpected error occurred.",
                details=[{"type": type(exc).__name__}],
            ).model_dump(),
        )
