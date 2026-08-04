from musicclean.orion.application import ServiceHealth


def test_service_health_is_transport_neutral() -> None:
    health = ServiceHealth(
        service="musicclean-orion",
        status="ok",
        schema_version=9,
    )

    assert health.service == "musicclean-orion"
    assert health.status == "ok"
    assert health.schema_version == 9
