"""Provider-neutral telemetry export contracts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class TelemetryEvent:
    name: str
    fields: dict[str, Any]
    emitted_at: datetime

    @classmethod
    def now(cls, name: str, fields: dict[str, Any]) -> TelemetryEvent:
        return cls(name=name, fields=fields, emitted_at=datetime.now(UTC))


class TelemetryExporter(Protocol):
    def export(self, event: TelemetryEvent) -> None: ...


class NullTelemetryExporter:
    def export(self, event: TelemetryEvent) -> None:
        del event


class CompositeTelemetryExporter:
    def __init__(self, exporters: tuple[TelemetryExporter, ...]) -> None:
        self._exporters = exporters

    def export(self, event: TelemetryEvent) -> None:
        for exporter in self._exporters:
            exporter.export(event)


class SafeTelemetryExporter:
    """Isolate exporter failures from request/runtime processing."""

    def __init__(self, exporter: TelemetryExporter) -> None:
        self._exporter = exporter

    def export(self, event: TelemetryEvent) -> None:
        try:
            self._exporter.export(event)
        except Exception:
            return
