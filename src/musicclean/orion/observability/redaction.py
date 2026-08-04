"""Secret-safe telemetry redaction."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

_SECRET_KEYS = frozenset({"api_key", "authorization", "password", "secret", "token", "x-api-key"})


def redact_mapping(values: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: "[REDACTED]" if key.lower() in _SECRET_KEYS else value for key, value in values.items()
    }
