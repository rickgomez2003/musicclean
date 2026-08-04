from pathlib import Path

from fastapi.testclient import TestClient

from musicclean.orion.adapters.sqlite import CURRENT_SCHEMA_VERSION
from musicclean.orion.runtime import RuntimeConfig, bootstrap_runtime


def test_runtime_bootstrap_migrates_database_and_serves_health(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "data" / "orion.db"
    runtime = bootstrap_runtime(
        RuntimeConfig(
            database_path=db_path,
            startup_reconcile=True,
        )
    )

    assert db_path.exists()
    assert runtime.schema_version == CURRENT_SCHEMA_VERSION

    response = TestClient(runtime.app).get("/v1/health")
    assert response.status_code == 200
    assert response.json()["schema_version"] == CURRENT_SCHEMA_VERSION


def test_runtime_bootstrap_can_skip_startup_reconciliation(
    tmp_path: Path,
) -> None:
    runtime = bootstrap_runtime(
        RuntimeConfig(
            database_path=tmp_path / "orion.db",
            startup_reconcile=False,
        )
    )

    assert runtime.schema_version == CURRENT_SCHEMA_VERSION
