"""SQLite persistence adapter for Orion."""

from musicclean.orion.adapters.sqlite.connection import connect_sqlite
from musicclean.orion.adapters.sqlite.decision_repository import SqliteDecisionRepository
from musicclean.orion.adapters.sqlite.evidence_repository import SqliteEvidenceRepository
from musicclean.orion.adapters.sqlite.execution_repository import (
    SqliteExecutionRepository,
)
from musicclean.orion.adapters.sqlite.knowledge_repository import (
    SqliteKnowledgeRepository,
)
from musicclean.orion.adapters.sqlite.migrations import CURRENT_SCHEMA_VERSION, migrate
from musicclean.orion.adapters.sqlite.review_repositories import (
    SqliteActionPlanRepository,
    SqliteAuthorizationRepository,
    SqliteReviewRepository,
)
from musicclean.orion.adapters.sqlite.unit_of_work import SqliteUnitOfWork

__all__ = [
    "CURRENT_SCHEMA_VERSION",
    "SqliteActionPlanRepository",
    "SqliteAuthorizationRepository",
    "SqliteDecisionRepository",
    "SqliteEvidenceRepository",
    "SqliteExecutionRepository",
    "SqliteKnowledgeRepository",
    "SqliteReviewRepository",
    "SqliteUnitOfWork",
    "connect_sqlite",
    "migrate",
]
