"""Structured event logging."""

from __future__ import annotations

import json
import logging
from collections.abc import Mapping
from typing import Any

from musicclean.orion.observability.redaction import redact_mapping
from musicclean.orion.observability.telemetry import (
    NullTelemetryExporter,
    TelemetryEvent,
    TelemetryExporter,
)


class StructuredEventLogger:
    def __init__(
        self,
        name: str = "musicclean.orion",
        exporter: TelemetryExporter | None = None,
    ) -> None:
        self._logger = logging.getLogger(name)
        self._exporter = exporter or NullTelemetryExporter()

    def info(self, event: str, **fields: Any) -> None:
        self._emit(logging.INFO, event, fields)

    def _emit(
        self,
        level: int,
        event: str,
        fields: Mapping[str, Any],
    ) -> None:
        redacted = redact_mapping(fields)
        payload = {"event": event, **redacted}
        self._logger.log(
            level,
            json.dumps(payload, sort_keys=True, default=str),
        )
        self._exporter.export(TelemetryEvent.now(event, dict(redacted)))
