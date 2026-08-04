from pathlib import Path

import pytest

from musicclean.orion.runtime import RuntimeConfig


def test_opentelemetry_defaults_disabled() -> None:
    config = RuntimeConfig(database_path=Path("orion.db"))
    assert config.otel_endpoint is None
    assert config.otel_service_name == "musicclean-orion"


def test_opentelemetry_environment_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "MUSICCLEAN_ORION_OTEL_ENDPOINT",
        "http://localhost:4318/v1/traces",
    )
    monkeypatch.setenv(
        "MUSICCLEAN_ORION_OTEL_SERVICE_NAME",
        "musicclean-test",
    )

    config = RuntimeConfig.from_environment()

    assert config.otel_endpoint == "http://localhost:4318/v1/traces"
    assert config.otel_service_name == "musicclean-test"


def test_blank_opentelemetry_endpoint_is_treated_as_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MUSICCLEAN_ORION_OTEL_ENDPOINT", "   ")
    config = RuntimeConfig.from_environment()
    assert config.otel_endpoint is None
