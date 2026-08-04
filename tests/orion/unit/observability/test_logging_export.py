from musicclean.orion.observability import StructuredEventLogger, TelemetryEvent


class RecordingExporter:
    def __init__(self) -> None:
        self.events: list[TelemetryEvent] = []

    def export(self, event: TelemetryEvent) -> None:
        self.events.append(event)


def test_structured_logger_exports_redacted_event() -> None:
    exporter = RecordingExporter()
    logger = StructuredEventLogger("musicclean.orion.test.export", exporter)

    logger.info("runtime_started", api_key="secret", port=8765)

    assert len(exporter.events) == 1
    assert exporter.events[0].name == "runtime_started"
    assert exporter.events[0].fields["api_key"] == "[REDACTED]"
    assert exporter.events[0].fields["port"] == 8765
