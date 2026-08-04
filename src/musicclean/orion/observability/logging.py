"""Structured event logging."""

from __future__ import annotations

import json
import logging
from collections.abc import Mapping
from typing import Any

from musicclean.orion.observability.redaction import redact_mapping


class StructuredEventLogger:
    def __init__(self, name: str = "musicclean.orion") -> None:
        self._logger = logging.getLogger(name)

    def info(self, event: str, **fields: Any) -> None:
        self._emit(logging.INFO, event, fields)

    def _emit(self, level: int, event: str, fields: Mapping[str, Any]) -> None:
        payload = {"event": event, **redact_mapping(fields)}
        self._logger.log(level, json.dumps(payload, sort_keys=True, default=str))
