from musicclean.orion.observability.redaction import redact_mapping


def test_common_secret_fields_are_redacted() -> None:
    result = redact_mapping({"api_key": "secret", "host": "localhost"})
    assert result["api_key"] == "[REDACTED]"
    assert result["host"] == "localhost"
