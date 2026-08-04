from pathlib import Path

from musicclean.orion.runtime.deployment_validation import (
    validate_deployment_environment,
)


def test_local_deployment_is_valid_without_api_key() -> None:
    result = validate_deployment_environment(
        database_path=Path("orion.db"),
        host="127.0.0.1",
        api_key=None,
        allowed_hosts=("127.0.0.1", "localhost"),
    )

    assert result.valid is True
    assert result.errors == ()


def test_non_local_deployment_requires_api_key() -> None:
    result = validate_deployment_environment(
        database_path=Path("orion.db"),
        host="0.0.0.0",
        api_key=None,
        allowed_hosts=("localhost",),
    )

    assert result.valid is False
    assert "non-local binding requires an API key" in result.errors


def test_empty_allowed_hosts_are_rejected() -> None:
    result = validate_deployment_environment(
        database_path=Path("orion.db"),
        host="127.0.0.1",
        api_key=None,
        allowed_hosts=(),
    )

    assert result.valid is False
    assert "at least one allowed host is required" in result.errors
