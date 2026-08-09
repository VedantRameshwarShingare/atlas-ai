"""Request-ID middleware for correlating HTTP logs."""

from __future__ import annotations

from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging.logger import get_logger
from app.core.logging.request_context import reset_request_id, set_request_id

request_logger = get_logger(__name__)


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Create one UUID request identifier and return it in every HTTP response."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Bind a generated request ID while downstream middleware and routes execute."""
        request_id = str(uuid4())
        token = set_request_id(request_id)
        try:
            request_logger.info("request_started")
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            request_logger.info("request_completed")
            return response
        finally:
            reset_request_id(token)
