from pathlib import Path

import pytest

from musicclean.orion.runtime.deployment import DeploymentPaths


def test_deployment_paths_have_safe_relative_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for name in (
        "MUSICCLEAN_ORION_STATE_DIR",
        "MUSICCLEAN_ORION_LOG_DIR",
        "MUSICCLEAN_ORION_TELEMETRY_DIR",
    ):
        monkeypatch.delenv(name, raising=False)

    paths = DeploymentPaths.from_environment()

    assert paths.state_dir == Path("var/orion")
    assert paths.log_dir == Path("var/orion/log")
    assert paths.telemetry_dir == Path("var/orion/telemetry")


def test_deployment_paths_can_be_overridden(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MUSICCLEAN_ORION_STATE_DIR", "state")
    monkeypatch.setenv("MUSICCLEAN_ORION_LOG_DIR", "logs")
    monkeypatch.setenv("MUSICCLEAN_ORION_TELEMETRY_DIR", "telemetry")

    paths = DeploymentPaths.from_environment()

    assert paths == DeploymentPaths(
        Path("state"),
        Path("logs"),
        Path("telemetry"),
    )


def test_deployment_paths_ensure_directories(tmp_path: Path) -> None:
    paths = DeploymentPaths(
        tmp_path / "state",
        tmp_path / "logs",
        tmp_path / "telemetry",
    )

    paths.ensure()

    assert paths.state_dir.is_dir()
    assert paths.log_dir.is_dir()
    assert paths.telemetry_dir.is_dir()
