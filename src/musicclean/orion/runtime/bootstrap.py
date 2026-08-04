"""Concrete runtime composition for Orion."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from fastapi import FastAPI

from musicclean.orion.adapters.filesystem import LocalFilesystemMutator
from musicclean.orion.adapters.http_host import HttpHostConfig, create_fastapi_app
from musicclean.orion.adapters.sqlite import (
    CURRENT_SCHEMA_VERSION,
    SqliteUnitOfWork,
    connect_sqlite,
    migrate,
)
from musicclean.orion.application import (
    OrionService,
    StartupRecoverySweep,
    startup_recovery_sweep,
)
from musicclean.orion.ports import UnitOfWork
from musicclean.orion.runtime.clock import UtcSystemClock
from musicclean.orion.runtime.config import RuntimeConfig


class SqliteUnitOfWorkFactory:
    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path

    def __call__(self) -> UnitOfWork:
        return SqliteUnitOfWork(self._database_path)


@dataclass(frozen=True, slots=True)
class OrionRuntime:
    config: RuntimeConfig
    service: OrionService
    app: FastAPI
    schema_version: int


def bootstrap_runtime(config: RuntimeConfig) -> OrionRuntime:
    """Build concrete Orion infrastructure and validate persistence."""
    config.database_path.parent.mkdir(parents=True, exist_ok=True)

    connection = connect_sqlite(config.database_path)
    try:
        schema_version = migrate(connection)
    finally:
        connection.close()

    if schema_version != CURRENT_SCHEMA_VERSION:
        raise RuntimeError("database schema version does not match runtime schema version")

    filesystem = LocalFilesystemMutator()
    clock = UtcSystemClock()

    uow_factory = SqliteUnitOfWorkFactory(config.database_path)

    service = OrionService(
        filesystem=filesystem,
        clock=clock,
        uow_factory=uow_factory,
        schema_version=schema_version,
    )

    if config.startup_reconcile:
        startup_recovery_sweep(
            StartupRecoverySweep(),
            filesystem,
            clock,
            uow_factory,
        )

    app = create_fastapi_app(
        service,
        HttpHostConfig(version="0.6.21"),
    )
    return OrionRuntime(
        config=config,
        service=service,
        app=app,
        schema_version=schema_version,
    )


def create_runtime_app(config: RuntimeConfig | None = None) -> FastAPI:
    """ASGI factory-friendly entry point."""
    return bootstrap_runtime(config or RuntimeConfig.from_environment()).app


RuntimeFactory = Callable[[], FastAPI]
