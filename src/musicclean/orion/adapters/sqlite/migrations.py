"""Versioned Orion SQLite schema migrations."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Migration:
    version: int
    description: str
    sql: str


MIGRATIONS: tuple[Migration, ...] = (
    Migration(
        1,
        "create Orion core-domain schema",
        """
        CREATE TABLE orion_libraries (id TEXT PRIMARY KEY, name TEXT NOT NULL);
        CREATE TABLE orion_artists (
            id TEXT PRIMARY KEY, name TEXT NOT NULL, sort_name TEXT
        );
        CREATE TABLE orion_albums (id TEXT PRIMARY KEY, title TEXT NOT NULL);
        CREATE TABLE orion_editions (
            id TEXT PRIMARY KEY, album_id TEXT NOT NULL, release_label TEXT,
            media_format TEXT, catalog_number TEXT, barcode TEXT,
            FOREIGN KEY (album_id) REFERENCES orion_albums(id)
        );
        CREATE TABLE orion_discs (
            id TEXT PRIMARY KEY, edition_id TEXT NOT NULL,
            position INTEGER NOT NULL CHECK (position >= 1), title TEXT,
            FOREIGN KEY (edition_id) REFERENCES orion_editions(id),
            UNIQUE (edition_id, position)
        );
        CREATE TABLE orion_recordings (
            id TEXT PRIMARY KEY, title TEXT NOT NULL,
            duration_ms INTEGER CHECK (duration_ms IS NULL OR duration_ms >= 0)
        );
        CREATE TABLE orion_track_appearances (
            id TEXT PRIMARY KEY, disc_id TEXT NOT NULL,
            recording_id TEXT NOT NULL,
            position INTEGER NOT NULL CHECK (position >= 1), title_override TEXT,
            FOREIGN KEY (disc_id) REFERENCES orion_discs(id),
            FOREIGN KEY (recording_id) REFERENCES orion_recordings(id),
            UNIQUE (disc_id, position)
        );
        CREATE TABLE orion_audio_files (
            id TEXT PRIMARY KEY, recording_id TEXT,
            location TEXT NOT NULL UNIQUE,
            size_bytes INTEGER NOT NULL CHECK (size_bytes >= 0),
            FOREIGN KEY (recording_id) REFERENCES orion_recordings(id)
        );
        """,
    ),
    Migration(
        2,
        "add provenance-backed evidence records",
        """
        CREATE TABLE orion_evidence (
            id TEXT PRIMARY KEY, subject_id TEXT NOT NULL, kind TEXT NOT NULL,
            value_type TEXT NOT NULL, value_text TEXT, value_integer INTEGER,
            value_real REAL, value_boolean INTEGER, provider TEXT NOT NULL,
            provider_version TEXT, warning TEXT, observed_at TEXT NOT NULL
        );
        """,
    ),
    Migration(
        3,
        "add inferred knowledge facts",
        """
        CREATE TABLE orion_knowledge (
            id TEXT PRIMARY KEY, subject_id TEXT NOT NULL, kind TEXT NOT NULL,
            value_type TEXT NOT NULL, value_text TEXT, value_integer INTEGER,
            value_real REAL, value_boolean INTEGER,
            confidence REAL NOT NULL, rule_id TEXT NOT NULL,
            rule_version TEXT NOT NULL, inferred_at TEXT NOT NULL
        );
        CREATE TABLE orion_knowledge_evidence (
            knowledge_id TEXT NOT NULL, evidence_id TEXT NOT NULL,
            ordinal INTEGER NOT NULL, PRIMARY KEY (knowledge_id, evidence_id)
        );
        """,
    ),
    Migration(
        4,
        "add explainable decision recommendations",
        """
        CREATE TABLE orion_decisions (
            id TEXT PRIMARY KEY, subject_id TEXT NOT NULL, action TEXT NOT NULL,
            confidence REAL NOT NULL, rationale TEXT NOT NULL,
            rule_id TEXT NOT NULL, rule_version TEXT NOT NULL,
            decided_at TEXT NOT NULL, risk TEXT
        );
        CREATE TABLE orion_decision_knowledge (
            decision_id TEXT NOT NULL, knowledge_id TEXT NOT NULL,
            ordinal INTEGER NOT NULL, PRIMARY KEY (decision_id, knowledge_id)
        );
        """,
    ),
    Migration(
        5,
        "add review authorization and quarantine planning",
        """
        CREATE TABLE orion_decision_reviews (
            id TEXT PRIMARY KEY, decision_id TEXT NOT NULL,
            outcome TEXT NOT NULL, reviewed_by TEXT NOT NULL,
            reviewed_at TEXT NOT NULL, note TEXT
        );
        CREATE TABLE orion_authorizations (
            id TEXT PRIMARY KEY, decision_id TEXT NOT NULL,
            review_id TEXT NOT NULL, granted_by TEXT NOT NULL,
            granted_at TEXT NOT NULL
        );
        CREATE TABLE orion_action_plans (
            id TEXT PRIMARY KEY, decision_id TEXT NOT NULL,
            authorization_id TEXT NOT NULL, action TEXT NOT NULL,
            source_location TEXT NOT NULL, target_location TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """,
    ),
    Migration(
        6,
        "add filesystem execution audit records",
        """
        CREATE TABLE orion_executions (
            id TEXT PRIMARY KEY, action_plan_id TEXT NOT NULL,
            kind TEXT NOT NULL, source_location TEXT NOT NULL,
            target_location TEXT NOT NULL, executed_by TEXT NOT NULL,
            executed_at TEXT NOT NULL
        );
        CREATE UNIQUE INDEX uq_orion_execution_plan_kind
            ON orion_executions(action_plan_id, kind);
        """,
    ),
    Migration(
        7,
        "add reconciliation findings",
        """
        CREATE TABLE orion_reconciliation_findings (
            id TEXT PRIMARY KEY, action_plan_id TEXT NOT NULL,
            status TEXT NOT NULL, proposed_action TEXT NOT NULL,
            source_exists INTEGER NOT NULL, target_exists INTEGER NOT NULL,
            has_quarantine_audit INTEGER NOT NULL,
            has_restore_audit INTEGER NOT NULL,
            detail TEXT NOT NULL, checked_at TEXT NOT NULL
        );
        """,
    ),
    Migration(
        8,
        "add operator-approved recovery audit metadata",
        """
        ALTER TABLE orion_executions
            ADD COLUMN origin TEXT NOT NULL DEFAULT 'direct';
        ALTER TABLE orion_executions
            ADD COLUMN recovery_finding_id TEXT;
        CREATE TABLE orion_recovery_approvals (
            id TEXT PRIMARY KEY, finding_id TEXT NOT NULL,
            kind TEXT NOT NULL, approved_by TEXT NOT NULL,
            approved_at TEXT NOT NULL, note TEXT
        );
        CREATE TABLE orion_recovery_records (
            id TEXT PRIMARY KEY, finding_id TEXT NOT NULL,
            approval_id TEXT NOT NULL UNIQUE, execution_id TEXT NOT NULL UNIQUE,
            kind TEXT NOT NULL, recovered_by TEXT NOT NULL,
            recovered_at TEXT NOT NULL
        );
        """,
    ),
    Migration(
        9,
        "add idempotency and action-plan leases",
        """
        CREATE TABLE orion_idempotency (
            key TEXT PRIMARY KEY,
            operation TEXT NOT NULL,
            subject_id TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            completed_at TEXT
        );

        CREATE TABLE orion_action_plan_leases (
            id TEXT PRIMARY KEY,
            action_plan_id TEXT NOT NULL UNIQUE,
            owner TEXT NOT NULL,
            acquired_at TEXT NOT NULL,
            expires_at TEXT NOT NULL
        );

        CREATE INDEX idx_orion_idempotency_subject
            ON orion_idempotency(subject_id, operation);
        CREATE INDEX idx_orion_action_plan_leases_expires
            ON orion_action_plan_leases(expires_at);
        """,
    ),
)

CURRENT_SCHEMA_VERSION = MIGRATIONS[-1].version


def _ensure_migration_table(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS orion_schema_migrations (
            version INTEGER PRIMARY KEY,
            description TEXT NOT NULL,
            applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def _applied_versions(connection: sqlite3.Connection) -> set[int]:
    rows = connection.execute(
        "SELECT version FROM orion_schema_migrations ORDER BY version"
    ).fetchall()
    return {int(row[0]) for row in rows}


def migrate(connection: sqlite3.Connection) -> int:
    _ensure_migration_table(connection)
    applied = _applied_versions(connection)

    for migration in MIGRATIONS:
        if migration.version in applied:
            continue
        try:
            connection.executescript(migration.sql)
            connection.execute(
                """
                INSERT INTO orion_schema_migrations(version, description)
                VALUES (?, ?)
                """,
                (migration.version, migration.description),
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise

    versions = _applied_versions(connection)
    return max(versions, default=0)
