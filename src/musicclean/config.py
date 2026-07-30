from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class ConfigError(RuntimeError):
    """Raised when the MusicClean configuration is invalid."""


@dataclass(frozen=True, slots=True)
class DatabaseConfig:
    path: Path


@dataclass(frozen=True, slots=True)
class LoggingConfig:
    directory: Path
    level: str
    max_bytes: int
    backup_count: int


@dataclass(frozen=True, slots=True)
class ScannerConfig:
    follow_symlinks: bool
    include_hidden: bool
    batch_size: int
    extensions: frozenset[str]


@dataclass(frozen=True, slots=True)
class AppConfig:
    paths: dict[str, tuple[Path, ...]]
    database: DatabaseConfig
    logging: LoggingConfig
    scanner: ScannerConfig


def _resolve(base: Path, value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else (base / path).resolve()


def _require_mapping(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ConfigError(f"{name} must be a mapping")
    return value


def load_config(path: Path) -> AppConfig:
    config_path = path.expanduser().resolve()
    if not config_path.is_file():
        raise ConfigError(f"Configuration file does not exist: {config_path}")

    with config_path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}

    if not isinstance(raw, dict):
        raise ConfigError("Top-level configuration must be a mapping")

    base = config_path.parent
    raw_paths = _require_mapping(raw.get("paths", {}), "paths")
    paths: dict[str, tuple[Path, ...]] = {}
    for name, values in raw_paths.items():
        if not isinstance(name, str) or not isinstance(values, list):
            raise ConfigError(f"paths.{name} must be a list")
        paths[name] = tuple(_resolve(base, str(item)) for item in values)

    database = _require_mapping(raw.get("database", {}), "database")
    logging = _require_mapping(raw.get("logging", {}), "logging")
    scanner = _require_mapping(raw.get("scanner", {}), "scanner")

    extensions_raw = scanner.get("extensions", [])
    if not isinstance(extensions_raw, list):
        raise ConfigError("scanner.extensions must be a list")

    extensions = frozenset(
        ext.lower() if str(ext).startswith(".") else f".{str(ext).lower()}"
        for ext in extensions_raw
    )

    return AppConfig(
        paths=paths,
        database=DatabaseConfig(
            path=_resolve(base, str(database.get("path", ".musicclean/musicclean.db")))
        ),
        logging=LoggingConfig(
            directory=_resolve(base, str(logging.get("directory", ".musicclean/logs"))),
            level=str(logging.get("level", "INFO")).upper(),
            max_bytes=int(logging.get("max_bytes", 10_485_760)),
            backup_count=int(logging.get("backup_count", 5)),
        ),
        scanner=ScannerConfig(
            follow_symlinks=bool(scanner.get("follow_symlinks", False)),
            include_hidden=bool(scanner.get("include_hidden", False)),
            batch_size=max(1, int(scanner.get("batch_size", 1000))),
            extensions=extensions,
        ),
    )
