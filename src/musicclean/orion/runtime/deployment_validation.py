"""Deployment preflight validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class DeploymentValidation:
    valid: bool
    errors: tuple[str, ...]


def validate_deployment_environment(
    *,
    database_path: Path,
    host: str,
    api_key: str | None,
    allowed_hosts: tuple[str, ...],
) -> DeploymentValidation:
    errors: list[str] = []

    if not str(database_path).strip():
        errors.append("database path is required")

    if not host.strip():
        errors.append("host is required")

    local_hosts = {"127.0.0.1", "localhost", "::1"}
    if host not in local_hosts and not (api_key and api_key.strip()):
        errors.append("non-local binding requires an API key")

    if not allowed_hosts:
        errors.append("at least one allowed host is required")

    return DeploymentValidation(valid=not errors, errors=tuple(errors))
