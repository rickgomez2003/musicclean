"""FastAPI middleware for Orion runtime security."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import Request
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from musicclean.orion.adapters.http_host.security_policy import (
    RuntimeSecurityPolicy,
)

RequestHandler = Callable[[Request], Awaitable[Response]]


class OrionSecurityMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        *,
        policy: RuntimeSecurityPolicy,
    ) -> None:
        super().__init__(app)
        self._policy = policy

    async def dispatch(self, request: Request, call_next: RequestHandler) -> Response:
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                size = int(content_length)
            except ValueError:
                return _error(400, "invalid_content_length")
            if size > self._policy.max_request_bytes:
                return _error(413, "request_too_large")

        public = self._policy.public_health and request.url.path == "/v1/health"
        if (
            not public
            and self._policy.authentication_enabled
            and not self._policy.authenticates(request.headers.get("x-api-key"))
        ):
            return _error(401, "unauthorized")

        response = await call_next(request)
        _apply_security_headers(response)
        return response


def _error(status_code: int, code: str) -> JSONResponse:
    response = JSONResponse(status_code=status_code, content={"error": code})
    _apply_security_headers(response)
    return response


def _apply_security_headers(response: Response) -> None:
    response.headers["x-content-type-options"] = "nosniff"
    response.headers["x-frame-options"] = "DENY"
    response.headers["referrer-policy"] = "no-referrer"
    response.headers["cache-control"] = "no-store"
