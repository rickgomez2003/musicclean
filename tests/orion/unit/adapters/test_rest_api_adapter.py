from typing import Any, cast

from musicclean.orion.adapters.http import HttpRequest, RestApiAdapter
from musicclean.orion.application import OrionService, ServiceHealth


class FakeService:
    def health(self) -> ServiceHealth:
        return ServiceHealth("musicclean-orion", "ok", 9)


def _adapter() -> RestApiAdapter:
    return RestApiAdapter(cast(OrionService, cast(Any, FakeService())))


def test_health_route() -> None:
    response = _adapter().handle(HttpRequest("GET", "/v1/health"))
    assert response.status_code == 200
    assert response.body["status"] == "ok"


def test_unknown_route_is_404() -> None:
    response = _adapter().handle(HttpRequest("GET", "/v1/unknown"))
    assert response.status_code == 404
    assert response.body["error"] == "route_not_found"
