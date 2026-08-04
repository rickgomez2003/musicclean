"""Runtime configuration for the Orion process."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})
_FALSE_VALUES = frozenset({"0", "false", "no", "off"})
_LOCAL_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})


@dataclass(frozen=True, slots=True)
class RuntimeConfig:
    database_path: Path
    host: str = "127.0.0.1"
    port: int = 8765
    log_level: str = "info"
    startup_reconcile: bool = True
    api_key: str | None = None
    public_health: bool = True
    max_request_bytes: int = 1_048_576
    allowed_origins: tuple[str, ...] = ()
    allowed_hosts: tuple[str, ...] = ("127.0.0.1", "localhost")
    telemetry_jsonl_path: Path | None = None
    otel_endpoint: str | None = None
    otel_service_name: str = "musicclean-orion"

    def __post_init__(self) -> None:
        if not self.host.strip():
            raise ValueError("host must be non-empty")
        if not 1 <= self.port <= 65535:
            raise ValueError("port must be between 1 and 65535")
        if self.api_key is not None and not self.api_key.strip():
            raise ValueError("api_key cannot be blank")
        if self.max_request_bytes <= 0:
            raise ValueError("max_request_bytes must be positive")
        if not self.allowed_hosts:
            raise ValueError("allowed_hosts cannot be empty")
        if self.host not in _LOCAL_HOSTS and self.api_key is None:
            raise ValueError("non-local HTTP binding requires an API key")
        if self.otel_endpoint is not None and not self.otel_endpoint.strip():
            raise ValueError("otel_endpoint cannot be blank")
        if not self.otel_service_name.strip():
            raise ValueError("otel_service_name cannot be blank")

    @classmethod
    def from_environment(cls) -> RuntimeConfig:
        telemetry_path = _optional(os.environ.get("MUSICCLEAN_ORION_TELEMETRY_JSONL"))
        return cls(
            database_path=Path(os.environ.get("MUSICCLEAN_ORION_DATABASE", "orion.db")),
            host=os.environ.get("MUSICCLEAN_ORION_HOST", "127.0.0.1"),
            port=int(os.environ.get("MUSICCLEAN_ORION_PORT", "8765")),
            log_level=os.environ.get("MUSICCLEAN_ORION_LOG_LEVEL", "info").lower(),
            startup_reconcile=_parse_bool(
                os.environ.get("MUSICCLEAN_ORION_STARTUP_RECONCILE", "true")
            ),
            api_key=_optional(os.environ.get("MUSICCLEAN_ORION_API_KEY")),
            public_health=_parse_bool(os.environ.get("MUSICCLEAN_ORION_PUBLIC_HEALTH", "true")),
            max_request_bytes=int(os.environ.get("MUSICCLEAN_ORION_MAX_REQUEST_BYTES", "1048576")),
            allowed_origins=_csv(os.environ.get("MUSICCLEAN_ORION_ALLOWED_ORIGINS", "")),
            allowed_hosts=_csv(
                os.environ.get(
                    "MUSICCLEAN_ORION_ALLOWED_HOSTS",
                    "127.0.0.1,localhost",
                )
            ),
            telemetry_jsonl_path=Path(telemetry_path) if telemetry_path else None,
            otel_endpoint=_optional(os.environ.get("MUSICCLEAN_ORION_OTEL_ENDPOINT")),
            otel_service_name=os.environ.get(
                "MUSICCLEAN_ORION_OTEL_SERVICE_NAME",
                "musicclean-orion",
            ),
        )


def _parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False
    raise ValueError("expected boolean value")


def _optional(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _csv(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())
