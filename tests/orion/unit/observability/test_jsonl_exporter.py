import json
from datetime import UTC, datetime
from pathlib import Path

from musicclean.orion.observability import JsonlTelemetryExporter, TelemetryEvent


def test_jsonl_exporter_appends_redacted_event(tmp_path: Path) -> None:
    path = tmp_path / "telemetry" / "events.jsonl"
    exporter = JsonlTelemetryExporter(path)

    exporter.export(
        TelemetryEvent(
            name="request",
            fields={"api_key": "secret", "status_code": 200},
            emitted_at=datetime(2026, 8, 4, tzinfo=UTC),
        )
    )

    payload = json.loads(path.read_text(encoding="utf-8").strip())

    assert payload["name"] == "request"
    assert payload["fields"]["api_key"] == "[REDACTED]"
    assert payload["fields"]["status_code"] == 200
