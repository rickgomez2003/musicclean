from pathlib import Path

from fastapi.testclient import TestClient

from musicclean.orion.runtime import RuntimeConfig, bootstrap_runtime


def _client(
    tmp_path: Path,
    *,
    public_health: bool = True,
    max_request_bytes: int = 1_048_576,
) -> TestClient:
    runtime = bootstrap_runtime(
        RuntimeConfig(
            database_path=tmp_path / "orion.db",
            api_key="secret",
            public_health=public_health,
            max_request_bytes=max_request_bytes,
        )
    )
    return TestClient(
        runtime.app,
        base_url="http://localhost",
    )


def test_docs_require_api_key_but_public_health_does_not(tmp_path: Path) -> None:
    client = _client(tmp_path)

    assert client.get("/v1/health").status_code == 200
    assert client.get("/docs").status_code == 401
    assert client.get("/docs", headers={"x-api-key": "secret"}).status_code == 200


def test_private_health_requires_api_key(tmp_path: Path) -> None:
    client = _client(tmp_path, public_health=False)

    assert client.get("/v1/health").status_code == 401

    response = client.get(
        "/v1/health",
        headers={"x-api-key": "secret"},
    )

    assert response.status_code == 200


def test_wrong_api_key_is_rejected(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.get(
        "/docs",
        headers={"x-api-key": "wrong"},
    )

    assert response.status_code == 401
    assert response.json() == {"error": "unauthorized"}


def test_security_headers_are_added(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.get("/v1/health")

    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert response.headers["cache-control"] == "no-store"


def test_invalid_content_length_is_rejected(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.post(
        "/v1/action-plans/not-an-id/quarantine",
        headers={
            "x-api-key": "secret",
            "content-length": "invalid",
        },
        content=b"{}",
    )

    assert response.status_code == 400
    assert response.json() == {"error": "invalid_content_length"}


def test_oversized_request_is_rejected(tmp_path: Path) -> None:
    client = _client(
        tmp_path,
        max_request_bytes=8,
    )

    response = client.post(
        "/v1/action-plans/not-an-id/quarantine",
        headers={
            "x-api-key": "secret",
            "content-length": "999",
        },
        content=b"{}",
    )

    assert response.status_code == 413
    assert response.json() == {"error": "request_too_large"}
