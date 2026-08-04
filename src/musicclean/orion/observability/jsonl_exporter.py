"""Append-only JSON Lines telemetry exporter."""

from __future__ import annotations

import json
from pathlib import Path

from musicclean.orion.observability.redaction import redact_mapping
from musicclean.orion.observability.telemetry import TelemetryEvent


class JsonlTelemetryExporter:
    def __init__(self, path: Path) -> None:
        self._path = path

    def export(self, event: TelemetryEvent) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "name": event.name,
            "emitted_at": event.emitted_at.isoformat(),
            "fields": redact_mapping(event.fields),
        }
        with self._path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(payload, sort_keys=True, default=str))
            stream.write("\n")
