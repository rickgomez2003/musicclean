from musicclean.orion.observability.request_ids import normalize_request_id


def test_valid_request_id_is_preserved() -> None:
    assert normalize_request_id("request-123") == "request-123"


def test_invalid_request_id_is_replaced() -> None:
    value = normalize_request_id("bad request id")
    assert value != "bad request id"
    assert len(value) == 32
