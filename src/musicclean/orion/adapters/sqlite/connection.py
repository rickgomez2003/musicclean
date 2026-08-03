"""SQLite connection configuration for Orion."""

from __future__ import annotations

import sqlite3
from pathlib import Path


def connect_sqlite(path: str | Path) -> sqlite3.Connection:
    """Open an Orion SQLite connection with required safety settings."""
    connection = sqlite3.connect(str(path))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")

    foreign_keys = connection.execute("PRAGMA foreign_keys").fetchone()
    if foreign_keys is None or int(foreign_keys[0]) != 1:
        connection.close()
        raise RuntimeError("SQLite foreign key enforcement could not be enabled")

    return connection
