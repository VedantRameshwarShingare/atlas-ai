"""Bootstrap exception-handler registration point."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette import status

from app.api.responses import APIErrorResponse
from app.core.exceptions import ConversationNotFoundError, ProviderConfigurationError, ProviderUnavailableError


def add_exception_handlers(app: FastAPI) -> None:
    """Register a minimal safe fallback for unexpected HTTP application errors."""

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_: Request, __: Exception) -> JSONResponse:
        """Return a stable response without exposing internal exception details."""
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal Server Error"},
        )

    @app.exception_handler(ConversationNotFoundError)
    async def conversation_not_found_handler(_: Request, exc: ConversationNotFoundError) -> JSONResponse:
        """Avoid leaking another user's private conversation existence."""
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=APIErrorResponse(error="conversation_not_found", message=str(exc)).model_dump(mode="json"),
        )

    @app.exception_handler(ProviderConfigurationError)
    async def provider_configuration_handler(_: Request, exc: ProviderConfigurationError) -> JSONResponse:
        """Return a safe service-unavailable response for missing provider setup."""
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=APIErrorResponse(
                error="provider_configuration",
                message="AI provider configuration is unavailable",
            ).model_dump(mode="json"),
        )

    @app.exception_handler(ProviderUnavailableError)
    async def provider_unavailable_handler(_: Request, exc: ProviderUnavailableError) -> JSONResponse:
        """Return a safe service-unavailable response for provider failures."""
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=APIErrorResponse(
                error="provider_unavailable",
                message="AI provider is currently unavailable",
            ).model_dump(mode="json"),
        )
