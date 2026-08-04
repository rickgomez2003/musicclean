from musicclean.orion.adapters.http_host.security_policy import RuntimeSecurityPolicy


def test_api_key_policy() -> None:
    policy = RuntimeSecurityPolicy(api_key="secret")
    assert policy.authenticates("secret") is True
    assert policy.authenticates("wrong") is False
    assert policy.authenticates(None) is False
