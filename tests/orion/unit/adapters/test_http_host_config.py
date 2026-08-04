from musicclean.orion.adapters.http_host import HttpHostConfig


def test_http_host_defaults_are_versioned_and_documented() -> None:
    config = HttpHostConfig()

    assert config.title == "MusicClean Orion API"
    assert config.version == "0.6.20"
    assert config.docs_url == "/docs"
    assert config.openapi_url == "/openapi.json"
