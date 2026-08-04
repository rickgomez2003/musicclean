from typing import Any, cast

from fastapi.testclient import TestClient

from musicclean.orion.adapters.http_host import create_fastapi_app
from musicclean.orion.application import OrionService, ServiceHealth


class FakeService:
    def health(self) -> ServiceHealth:
        return ServiceHealth(
            service="musicclean-orion",
            status="ok",
            schema_version=9,
        )


def _client() -> TestClient:
    service = cast(OrionService, cast(Any, FakeService()))
    return TestClient(create_fastapi_app(service))


def test_fastapi_health_route() -> None:
    response = _client().get("/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "service": "musicclean-orion",
        "status": "ok",
        "schema_version": 9,
    }


def test_openapi_contains_versioned_orion_routes() -> None:
    response = _client().get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]

    assert "/v1/health" in paths
    assert "/v1/action-plans/{action_plan_id}/quarantine" in paths
    assert "/v1/action-plans/{action_plan_id}/restore" in paths
    assert "/v1/action-plans/{action_plan_id}/reconcile" in paths


def test_swagger_ui_is_enabled() -> None:
    response = _client().get("/docs")

    assert response.status_code == 200
    assert "swagger" in response.text.lower()
