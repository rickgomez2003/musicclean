"""Concrete runtime composition for Orion."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from fastapi import FastAPI

from musicclean.orion.adapters.filesystem import LocalFilesystemMutator
from musicclean.orion.adapters.http_host import HttpHostConfig, create_fastapi_app
from musicclean.orion.adapters.http_host.security_policy import RuntimeSecurityPolicy
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
from musicclean.orion.observability import RuntimeMetrics, StructuredEventLogger
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
    metrics: RuntimeMetrics


def bootstrap_runtime(config: RuntimeConfig) -> OrionRuntime:
    config.database_path.parent.mkdir(parents=True, exist_ok=True)

    logger = StructuredEventLogger()
    logger.info(
        "runtime_starting",
        database_path=str(config.database_path),
        host=config.host,
        port=config.port,
        api_key=config.api_key,
    )

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

    security = RuntimeSecurityPolicy(
        api_key=config.api_key,
        public_health=config.public_health,
        max_request_bytes=config.max_request_bytes,
        allowed_origins=config.allowed_origins,
        allowed_hosts=config.allowed_hosts,
    )

    metrics = RuntimeMetrics()

    app = create_fastapi_app(
        service,
        HttpHostConfig(version="0.6.23"),
        security,
        metrics,
        logger,
    )

    logger.info(
        "runtime_started",
        schema_version=schema_version,
        host=config.host,
        port=config.port,
    )

    return OrionRuntime(
        config=config,
        service=service,
        app=app,
        schema_version=schema_version,
        metrics=metrics,
    )


def create_runtime_app(config: RuntimeConfig | None = None) -> FastAPI:
    return bootstrap_runtime(config or RuntimeConfig.from_environment()).app


RuntimeFactory = Callable[[], FastAPI]
