from pathlib import Path

from fastapi.testclient import TestClient

from musicclean.orion.observability import RuntimeMetrics
from musicclean.orion.runtime import RuntimeConfig, bootstrap_runtime


def _runtime_client(
    tmp_path: Path,
    *,
    api_key: str | None = None,
) -> tuple[TestClient, RuntimeMetrics]:
    runtime = bootstrap_runtime(
        RuntimeConfig(
            database_path=tmp_path / "orion.db",
            api_key=api_key,
        )
    )

    return (
        TestClient(
            runtime.app,
            base_url="http://localhost",
        ),
        runtime.metrics,
    )


def test_request_id_is_generated_and_returned(tmp_path: Path) -> None:
    client, _ = _runtime_client(tmp_path)

    response = client.get("/v1/health")

    assert response.status_code == 200
    assert response.headers["x-request-id"]


def test_caller_request_id_is_preserved(tmp_path: Path) -> None:
    client, _ = _runtime_client(tmp_path)

    response = client.get(
        "/v1/health",
        headers={"x-request-id": "caller-123"},
    )

    assert response.status_code == 200
    assert response.headers["x-request-id"] == "caller-123"


def test_request_metrics_are_recorded(tmp_path: Path) -> None:
    client, metrics = _runtime_client(tmp_path)

    client.get("/v1/health")
    client.get("/v1/health")

    snapshot = metrics.snapshot()

    assert snapshot["requests_total"] == 2
    assert snapshot["errors_total"] == 0
    assert snapshot["request_duration_ms_total"] >= 0


def test_security_rejection_still_has_request_id_and_metrics(
    tmp_path: Path,
) -> None:
    client, metrics = _runtime_client(
        tmp_path,
        api_key="secret",
    )

    response = client.get("/docs")

    assert response.status_code == 401
    assert response.headers["x-request-id"]

    snapshot = metrics.snapshot()

    assert snapshot["requests_total"] == 1
    assert snapshot["errors_total"] == 1


def test_invalid_caller_request_id_is_replaced(tmp_path: Path) -> None:
    client, _ = _runtime_client(tmp_path)

    response = client.get(
        "/v1/health",
        headers={"x-request-id": "invalid request id"},
    )

    assert response.status_code == 200
    assert response.headers["x-request-id"] != "invalid request id"
    assert len(response.headers["x-request-id"]) == 32
