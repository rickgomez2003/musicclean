from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from musicclean.config import LoggingConfig


def configure_logging(config: LoggingConfig, verbose: bool = False) -> None:
    config.directory.mkdir(parents=True, exist_ok=True)

    level = logging.DEBUG if verbose else getattr(logging, config.level, logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()

    console = logging.StreamHandler()
    console.setLevel(level)
    console.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        config.directory / "musicclean.log",
        maxBytes=config.max_bytes,
        backupCount=config.backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)

    root.addHandler(console)
    root.addHandler(file_handler)
