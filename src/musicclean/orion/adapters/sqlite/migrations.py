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
        CREATE INDEX idx_orion_artists_name ON orion_artists(name);
        CREATE INDEX idx_orion_albums_title ON orion_albums(title);
        CREATE INDEX idx_orion_editions_album_id ON orion_editions(album_id);
        CREATE INDEX idx_orion_discs_edition_id ON orion_discs(edition_id);
        CREATE INDEX idx_orion_recordings_title ON orion_recordings(title);
        CREATE INDEX idx_orion_track_appearances_disc_id
            ON orion_track_appearances(disc_id);
        CREATE INDEX idx_orion_track_appearances_recording_id
            ON orion_track_appearances(recording_id);
        CREATE INDEX idx_orion_audio_files_recording_id
            ON orion_audio_files(recording_id);
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
        CREATE INDEX idx_orion_evidence_subject_id
            ON orion_evidence(subject_id);
        CREATE INDEX idx_orion_evidence_subject_kind
            ON orion_evidence(subject_id, kind);
        CREATE INDEX idx_orion_evidence_observed_at
            ON orion_evidence(observed_at);
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
            confidence REAL NOT NULL CHECK (
                confidence >= 0.0 AND confidence <= 1.0
            ),
            rule_id TEXT NOT NULL, rule_version TEXT NOT NULL,
            inferred_at TEXT NOT NULL
        );
        CREATE TABLE orion_knowledge_evidence (
            knowledge_id TEXT NOT NULL, evidence_id TEXT NOT NULL,
            ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
            PRIMARY KEY (knowledge_id, evidence_id),
            FOREIGN KEY (knowledge_id) REFERENCES orion_knowledge(id)
                ON DELETE CASCADE,
            FOREIGN KEY (evidence_id) REFERENCES orion_evidence(id)
        );
        CREATE INDEX idx_orion_knowledge_subject_id
            ON orion_knowledge(subject_id);
        CREATE INDEX idx_orion_knowledge_subject_kind
            ON orion_knowledge(subject_id, kind);
        CREATE INDEX idx_orion_knowledge_rule
            ON orion_knowledge(rule_id, rule_version);
        CREATE INDEX idx_orion_knowledge_evidence_evidence_id
            ON orion_knowledge_evidence(evidence_id);
        """,
    ),
    Migration(
        4,
        "add explainable decision recommendations",
        """
        CREATE TABLE orion_decisions (
            id TEXT PRIMARY KEY, subject_id TEXT NOT NULL, action TEXT NOT NULL,
            confidence REAL NOT NULL CHECK (
                confidence >= 0.0 AND confidence <= 1.0
            ),
            rationale TEXT NOT NULL, rule_id TEXT NOT NULL,
            rule_version TEXT NOT NULL, decided_at TEXT NOT NULL, risk TEXT
        );
        CREATE TABLE orion_decision_knowledge (
            decision_id TEXT NOT NULL, knowledge_id TEXT NOT NULL,
            ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
            PRIMARY KEY (decision_id, knowledge_id),
            FOREIGN KEY (decision_id) REFERENCES orion_decisions(id)
                ON DELETE CASCADE,
            FOREIGN KEY (knowledge_id) REFERENCES orion_knowledge(id)
        );
        CREATE INDEX idx_orion_decisions_subject_id
            ON orion_decisions(subject_id);
        CREATE INDEX idx_orion_decisions_subject_action
            ON orion_decisions(subject_id, action);
        CREATE INDEX idx_orion_decisions_rule
            ON orion_decisions(rule_id, rule_version);
        CREATE INDEX idx_orion_decision_knowledge_knowledge_id
            ON orion_decision_knowledge(knowledge_id);
        """,
    ),
    Migration(
        5,
        "add review authorization and quarantine planning",
        """
        CREATE TABLE orion_decision_reviews (
            id TEXT PRIMARY KEY, decision_id TEXT NOT NULL,
            outcome TEXT NOT NULL, reviewed_by TEXT NOT NULL,
            reviewed_at TEXT NOT NULL, note TEXT,
            FOREIGN KEY (decision_id) REFERENCES orion_decisions(id)
        );
        CREATE TABLE orion_authorizations (
            id TEXT PRIMARY KEY, decision_id TEXT NOT NULL,
            review_id TEXT NOT NULL, granted_by TEXT NOT NULL,
            granted_at TEXT NOT NULL,
            FOREIGN KEY (decision_id) REFERENCES orion_decisions(id),
            FOREIGN KEY (review_id) REFERENCES orion_decision_reviews(id)
        );
        CREATE TABLE orion_action_plans (
            id TEXT PRIMARY KEY, decision_id TEXT NOT NULL,
            authorization_id TEXT NOT NULL, action TEXT NOT NULL,
            source_location TEXT NOT NULL, target_location TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (decision_id) REFERENCES orion_decisions(id),
            FOREIGN KEY (authorization_id) REFERENCES orion_authorizations(id)
        );
        CREATE INDEX idx_orion_decision_reviews_decision
            ON orion_decision_reviews(decision_id, reviewed_at);
        CREATE INDEX idx_orion_authorizations_decision
            ON orion_authorizations(decision_id, granted_at);
        CREATE INDEX idx_orion_action_plans_decision
            ON orion_action_plans(decision_id, created_at);
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
            executed_at TEXT NOT NULL,
            FOREIGN KEY (action_plan_id) REFERENCES orion_action_plans(id)
        );
        CREATE UNIQUE INDEX uq_orion_execution_plan_kind
            ON orion_executions(action_plan_id, kind);
        CREATE INDEX idx_orion_executions_plan
            ON orion_executions(action_plan_id, executed_at);
        """,
    ),
    Migration(
        7,
        "add reconciliation findings",
        """
        CREATE TABLE orion_reconciliation_findings (
            id TEXT PRIMARY KEY, action_plan_id TEXT NOT NULL,
            status TEXT NOT NULL, proposed_action TEXT NOT NULL,
            source_exists INTEGER NOT NULL CHECK (source_exists IN (0, 1)),
            target_exists INTEGER NOT NULL CHECK (target_exists IN (0, 1)),
            has_quarantine_audit INTEGER NOT NULL CHECK (
                has_quarantine_audit IN (0, 1)
            ),
            has_restore_audit INTEGER NOT NULL CHECK (
                has_restore_audit IN (0, 1)
            ),
            detail TEXT NOT NULL, checked_at TEXT NOT NULL,
            FOREIGN KEY (action_plan_id) REFERENCES orion_action_plans(id)
        );
        CREATE INDEX idx_orion_reconciliation_plan
            ON orion_reconciliation_findings(action_plan_id, checked_at);
        CREATE INDEX idx_orion_reconciliation_status
            ON orion_reconciliation_findings(status);
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
            id TEXT PRIMARY KEY,
            finding_id TEXT NOT NULL,
            kind TEXT NOT NULL,
            approved_by TEXT NOT NULL,
            approved_at TEXT NOT NULL,
            note TEXT,
            FOREIGN KEY (finding_id) REFERENCES orion_reconciliation_findings(id)
        );

        CREATE TABLE orion_recovery_records (
            id TEXT PRIMARY KEY,
            finding_id TEXT NOT NULL,
            approval_id TEXT NOT NULL UNIQUE,
            execution_id TEXT NOT NULL UNIQUE,
            kind TEXT NOT NULL,
            recovered_by TEXT NOT NULL,
            recovered_at TEXT NOT NULL,
            FOREIGN KEY (finding_id) REFERENCES orion_reconciliation_findings(id),
            FOREIGN KEY (approval_id) REFERENCES orion_recovery_approvals(id),
            FOREIGN KEY (execution_id) REFERENCES orion_executions(id)
        );

        CREATE INDEX idx_orion_recovery_approvals_finding
            ON orion_recovery_approvals(finding_id, approved_at);
        CREATE INDEX idx_orion_recovery_records_finding
            ON orion_recovery_records(finding_id, recovered_at);
        CREATE INDEX idx_orion_executions_recovery_finding
            ON orion_executions(recovery_finding_id);
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
