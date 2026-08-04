from pathlib import Path

import pytest

from musicclean.orion.runtime import RuntimeConfig


def test_runtime_config_has_local_safe_defaults() -> None:
    config = RuntimeConfig(database_path=Path("orion.db"))

    assert config.host == "127.0.0.1"
    assert config.port == 8765
    assert config.startup_reconcile is True


def test_runtime_config_rejects_invalid_port() -> None:
    with pytest.raises(ValueError, match="port"):
        RuntimeConfig(database_path=Path("orion.db"), port=70000)


def test_runtime_config_rejects_blank_host() -> None:
    with pytest.raises(ValueError, match="host must be non-empty"):
        RuntimeConfig(
            database_path=Path("orion.db"),
            host="   ",
        )


def test_runtime_config_rejects_blank_api_key() -> None:
    with pytest.raises(ValueError, match="api_key cannot be blank"):
        RuntimeConfig(
            database_path=Path("orion.db"),
            api_key="   ",
        )


def test_runtime_config_rejects_non_positive_request_limit() -> None:
    with pytest.raises(ValueError, match="max_request_bytes must be positive"):
        RuntimeConfig(
            database_path=Path("orion.db"),
            max_request_bytes=0,
        )


def test_runtime_config_rejects_empty_allowed_hosts() -> None:
    with pytest.raises(ValueError, match="allowed_hosts cannot be empty"):
        RuntimeConfig(
            database_path=Path("orion.db"),
            allowed_hosts=(),
        )


def test_non_local_binding_requires_api_key() -> None:
    with pytest.raises(ValueError, match="non-local HTTP binding requires an API key"):
        RuntimeConfig(
            database_path=Path("orion.db"),
            host="0.0.0.0",
        )


def test_non_local_binding_is_allowed_with_api_key() -> None:
    config = RuntimeConfig(
        database_path=Path("orion.db"),
        host="0.0.0.0",
        api_key="secret",
    )

    assert config.host == "0.0.0.0"
    assert config.api_key == "secret"


def test_runtime_config_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MUSICCLEAN_ORION_DATABASE", "custom.db")
    monkeypatch.setenv("MUSICCLEAN_ORION_HOST", "localhost")
    monkeypatch.setenv("MUSICCLEAN_ORION_PORT", "9000")
    monkeypatch.setenv("MUSICCLEAN_ORION_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("MUSICCLEAN_ORION_STARTUP_RECONCILE", "false")
    monkeypatch.setenv("MUSICCLEAN_ORION_API_KEY", " secret ")
    monkeypatch.setenv("MUSICCLEAN_ORION_PUBLIC_HEALTH", "no")
    monkeypatch.setenv("MUSICCLEAN_ORION_MAX_REQUEST_BYTES", "2048")
    monkeypatch.setenv(
        "MUSICCLEAN_ORION_ALLOWED_ORIGINS",
        "https://example.com, https://music.example.com",
    )
    monkeypatch.setenv(
        "MUSICCLEAN_ORION_ALLOWED_HOSTS",
        "localhost, 127.0.0.1",
    )

    config = RuntimeConfig.from_environment()

    assert config.database_path == Path("custom.db")
    assert config.host == "localhost"
    assert config.port == 9000
    assert config.log_level == "debug"
    assert config.startup_reconcile is False
    assert config.api_key == "secret"
    assert config.public_health is False
    assert config.max_request_bytes == 2048
    assert config.allowed_origins == (
        "https://example.com",
        "https://music.example.com",
    )
    assert config.allowed_hosts == (
        "localhost",
        "127.0.0.1",
    )


def test_runtime_config_environment_rejects_invalid_boolean(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "MUSICCLEAN_ORION_STARTUP_RECONCILE",
        "maybe",
    )

    with pytest.raises(ValueError, match="expected boolean value"):
        RuntimeConfig.from_environment()
