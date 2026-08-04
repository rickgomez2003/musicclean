from datetime import UTC, datetime

from musicclean.orion.observability import (
    OpenTelemetryTelemetryExporter,
    TelemetryEvent,
)


def test_opentelemetry_exporter_maps_event_to_span_attributes() -> None:
    captured: list[tuple[str, dict[str, str | bool | int | float]]] = []

    def emit(
        name: str,
        attributes: dict[str, str | bool | int | float],
    ) -> None:
        captured.append((name, attributes))

    exporter = OpenTelemetryTelemetryExporter(emit)
    exporter.export(
        TelemetryEvent(
            name="http_request_completed",
            fields={
                "request_id": "req-123",
                "status_code": 200,
                "extra": {"nested": True},
                "none": None,
            },
            emitted_at=datetime(2026, 8, 4, tzinfo=UTC),
        )
    )

    name, attributes = captured[0]
    assert name == "http_request_completed"
    assert attributes["request_id"] == "req-123"
    assert attributes["status_code"] == 200
    assert attributes["extra"] == "{'nested': True}"
    assert attributes["none"] == "null"
    assert attributes["orion.event.emitted_at"].startswith("2026-08-04")
