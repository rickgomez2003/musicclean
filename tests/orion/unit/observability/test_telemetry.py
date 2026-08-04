from datetime import UTC, datetime

from musicclean.orion.observability.telemetry import (
    CompositeTelemetryExporter,
    NullTelemetryExporter,
    SafeTelemetryExporter,
    TelemetryEvent,
)


class RecordingExporter:
    def __init__(self) -> None:
        self.events: list[TelemetryEvent] = []

    def export(self, event: TelemetryEvent) -> None:
        self.events.append(event)


class FailingExporter:
    def export(self, event: TelemetryEvent) -> None:
        del event
        raise RuntimeError("boom")


def test_composite_exporter_fans_out() -> None:
    left = RecordingExporter()
    right = RecordingExporter()
    event = TelemetryEvent("test", {}, datetime.now(UTC))

    CompositeTelemetryExporter((left, right)).export(event)

    assert left.events == [event]
    assert right.events == [event]


def test_safe_exporter_isolates_failures() -> None:
    event = TelemetryEvent("test", {}, datetime.now(UTC))
    SafeTelemetryExporter(FailingExporter()).export(event)


def test_null_exporter_is_noop() -> None:
    event = TelemetryEvent("test", {}, datetime.now(UTC))
    NullTelemetryExporter().export(event)
