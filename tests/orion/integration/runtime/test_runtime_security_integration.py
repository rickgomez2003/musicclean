from pathlib import Path

from fastapi.testclient import TestClient

from musicclean.orion.runtime import RuntimeConfig, bootstrap_runtime


def test_docs_require_api_key_but_public_health_does_not(tmp_path: Path) -> None:
    runtime = bootstrap_runtime(
        RuntimeConfig(
            database_path=tmp_path / "orion.db",
            api_key="secret",
            public_health=True,
        )
    )
    client = TestClient(
        runtime.app,
        base_url="http://localhost",
    )

    assert client.get("/v1/health").status_code == 200
    assert client.get("/docs").status_code == 401
    assert client.get("/docs", headers={"x-api-key": "secret"}).status_code == 200
