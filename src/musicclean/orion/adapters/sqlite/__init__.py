"""SQLite persistence adapter for Orion."""

from musicclean.orion.adapters.sqlite.connection import connect_sqlite
from musicclean.orion.adapters.sqlite.evidence_repository import SqliteEvidenceRepository
from musicclean.orion.adapters.sqlite.migrations import CURRENT_SCHEMA_VERSION, migrate
from musicclean.orion.adapters.sqlite.unit_of_work import SqliteUnitOfWork

__all__ = [
    "CURRENT_SCHEMA_VERSION",
    "SqliteEvidenceRepository",
    "SqliteUnitOfWork",
    "connect_sqlite",
    "migrate",
]
