"""Runtime configuration for the Orion process."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})
_FALSE_VALUES = frozenset({"0", "false", "no", "off"})


@dataclass(frozen=True, slots=True)
class RuntimeConfig:
    database_path: Path
    host: str = "127.0.0.1"
    port: int = 8765
    log_level: str = "info"
    startup_reconcile: bool = True

    def __post_init__(self) -> None:
        if not str(self.database_path):
            raise ValueError("database_path is required")
        if not self.host.strip():
            raise ValueError("host must be non-empty")
        if not 1 <= self.port <= 65535:
            raise ValueError("port must be between 1 and 65535")
        if self.log_level not in {"critical", "error", "warning", "info", "debug", "trace"}:
            raise ValueError("unsupported log level")

    @classmethod
    def from_environment(cls) -> RuntimeConfig:
        return cls(
            database_path=Path(os.environ.get("MUSICCLEAN_ORION_DATABASE", "orion.db")),
            host=os.environ.get("MUSICCLEAN_ORION_HOST", "127.0.0.1"),
            port=_parse_port(os.environ.get("MUSICCLEAN_ORION_PORT", "8765")),
            log_level=os.environ.get(
                "MUSICCLEAN_ORION_LOG_LEVEL",
                "info",
            ).lower(),
            startup_reconcile=_parse_bool(
                os.environ.get(
                    "MUSICCLEAN_ORION_STARTUP_RECONCILE",
                    "true",
                )
            ),
        )


def _parse_port(value: str) -> int:
    try:
        port = int(value)
    except ValueError as exc:
        raise ValueError("MUSICCLEAN_ORION_PORT must be an integer") from exc
    return port


def _parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False
    raise ValueError("MUSICCLEAN_ORION_STARTUP_RECONCILE must be a boolean value")
