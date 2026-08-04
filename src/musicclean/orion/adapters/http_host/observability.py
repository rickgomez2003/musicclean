"""HTTP observability middleware."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from time import perf_counter

from fastapi import Request
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from musicclean.orion.observability import (
    RuntimeMetrics,
    StructuredEventLogger,
    normalize_request_id,
)

RequestHandler = Callable[[Request], Awaitable[Response]]


class OrionObservabilityMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        *,
        metrics: RuntimeMetrics,
        logger: StructuredEventLogger,
    ) -> None:
        super().__init__(app)
        self._metrics = metrics
        self._logger = logger

    async def dispatch(self, request: Request, call_next: RequestHandler) -> Response:
        request_id = normalize_request_id(request.headers.get("x-request-id"))
        request.state.request_id = request_id
        started = perf_counter()
        response = await call_next(request)
        duration_ms = (perf_counter() - started) * 1000.0
        response.headers["x-request-id"] = request_id
        self._metrics.record_request(response.status_code, duration_ms)
        self._logger.info(
            "http_request_completed",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 3),
        )
        return response
