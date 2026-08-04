import pytest

from musicclean.orion.adapters.http_host.security_policy import RuntimeSecurityPolicy


def test_api_key_policy() -> None:
    policy = RuntimeSecurityPolicy(api_key="secret")
    assert policy.authenticates("secret") is True
    assert policy.authenticates("wrong") is False
    assert policy.authenticates(None) is False


def test_authentication_disabled_without_api_key() -> None:
    policy = RuntimeSecurityPolicy(api_key=None)

    assert policy.authentication_enabled is False
    assert policy.authenticates(None) is True
    assert policy.authenticates("anything") is True


def test_blank_api_key_is_rejected() -> None:
    with pytest.raises(ValueError, match="api_key cannot be blank"):
        RuntimeSecurityPolicy(api_key="   ")


def test_non_positive_request_limit_is_rejected() -> None:
    with pytest.raises(ValueError, match="max_request_bytes must be positive"):
        RuntimeSecurityPolicy(
            api_key=None,
            max_request_bytes=0,
        )


def test_empty_allowed_hosts_is_rejected() -> None:
    with pytest.raises(ValueError, match="allowed_hosts cannot be empty"):
        RuntimeSecurityPolicy(
            api_key=None,
            allowed_hosts=(),
        )
