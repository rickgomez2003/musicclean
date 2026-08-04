"""FastAPI host that delegates transport work to RestApiAdapter."""

from __future__ import annotations

from typing import Annotated

from fastapi import Body, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware

from musicclean.orion.adapters.http import HttpRequest, HttpResponse, RestApiAdapter
from musicclean.orion.adapters.http_host.config import HttpHostConfig
from musicclean.orion.adapters.http_host.models import ActionRequestBody
from musicclean.orion.adapters.http_host.security import OrionSecurityMiddleware
from musicclean.orion.adapters.http_host.security_policy import RuntimeSecurityPolicy
from musicclean.orion.application import OrionService


def create_fastapi_app(
    service: OrionService,
    config: HttpHostConfig | None = None,
    security: RuntimeSecurityPolicy | None = None,
) -> FastAPI:
    resolved = config or HttpHostConfig()
    policy = security or RuntimeSecurityPolicy(api_key=None)
    adapter = RestApiAdapter(service)

    app = FastAPI(
        title=resolved.title,
        version=resolved.version,
        docs_url=resolved.docs_url,
        redoc_url=resolved.redoc_url,
        openapi_url=resolved.openapi_url,
    )
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=list(policy.allowed_hosts),
    )
    if policy.allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(policy.allowed_origins),
            allow_credentials=False,
            allow_methods=["GET", "POST"],
            allow_headers=["content-type", "x-api-key"],
        )
    app.add_middleware(OrionSecurityMiddleware, policy=policy)

    def convert(response: HttpResponse) -> JSONResponse:
        return JSONResponse(
            status_code=response.status_code,
            content=response.body,
            headers=response.headers,
        )

    @app.get("/v1/health", tags=["system"])
    def health() -> JSONResponse:
        return convert(adapter.handle(HttpRequest("GET", "/v1/health")))

    @app.post("/v1/action-plans/{action_plan_id}/quarantine", tags=["execution"])
    def quarantine(
        action_plan_id: str,
        body: Annotated[ActionRequestBody, Body()],
    ) -> JSONResponse:
        return convert(
            adapter.handle(
                HttpRequest(
                    "POST",
                    f"/v1/action-plans/{action_plan_id}/quarantine",
                    body.model_dump(),
                )
            )
        )

    @app.post("/v1/action-plans/{action_plan_id}/restore", tags=["execution"])
    def restore(
        action_plan_id: str,
        body: Annotated[ActionRequestBody, Body()],
    ) -> JSONResponse:
        return convert(
            adapter.handle(
                HttpRequest(
                    "POST",
                    f"/v1/action-plans/{action_plan_id}/restore",
                    body.model_dump(),
                )
            )
        )

    @app.post("/v1/action-plans/{action_plan_id}/reconcile", tags=["reconciliation"])
    def reconcile(action_plan_id: str) -> JSONResponse:
        return convert(
            adapter.handle(
                HttpRequest(
                    "POST",
                    f"/v1/action-plans/{action_plan_id}/reconcile",
                )
            )
        )

    return app
