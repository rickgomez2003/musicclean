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
        CREATE TABLE orion_libraries (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL
        );
        CREATE TABLE orion_artists (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            sort_name TEXT
        );
        CREATE TABLE orion_albums (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL
        );
        CREATE TABLE orion_editions (
            id TEXT PRIMARY KEY,
            album_id TEXT NOT NULL,
            release_label TEXT,
            media_format TEXT,
            catalog_number TEXT,
            barcode TEXT,
            FOREIGN KEY (album_id) REFERENCES orion_albums(id)
        );
        CREATE TABLE orion_discs (
            id TEXT PRIMARY KEY,
            edition_id TEXT NOT NULL,
            position INTEGER NOT NULL CHECK (position >= 1),
            title TEXT,
            FOREIGN KEY (edition_id) REFERENCES orion_editions(id),
            UNIQUE (edition_id, position)
        );
        CREATE TABLE orion_recordings (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            duration_ms INTEGER CHECK (
                duration_ms IS NULL OR duration_ms >= 0
            )
        );
        CREATE TABLE orion_track_appearances (
            id TEXT PRIMARY KEY,
            disc_id TEXT NOT NULL,
            recording_id TEXT NOT NULL,
            position INTEGER NOT NULL CHECK (position >= 1),
            title_override TEXT,
            FOREIGN KEY (disc_id) REFERENCES orion_discs(id),
            FOREIGN KEY (recording_id) REFERENCES orion_recordings(id),
            UNIQUE (disc_id, position)
        );
        CREATE TABLE orion_audio_files (
            id TEXT PRIMARY KEY,
            recording_id TEXT,
            location TEXT NOT NULL UNIQUE,
            size_bytes INTEGER NOT NULL CHECK (size_bytes >= 0),
            FOREIGN KEY (recording_id) REFERENCES orion_recordings(id)
        );
        CREATE INDEX idx_orion_artists_name
            ON orion_artists(name);
        CREATE INDEX idx_orion_albums_title
            ON orion_albums(title);
        CREATE INDEX idx_orion_editions_album_id
            ON orion_editions(album_id);
        CREATE INDEX idx_orion_discs_edition_id
            ON orion_discs(edition_id);
        CREATE INDEX idx_orion_recordings_title
            ON orion_recordings(title);
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
            id TEXT PRIMARY KEY,
            subject_id TEXT NOT NULL,
            kind TEXT NOT NULL,
            value_type TEXT NOT NULL,
            value_text TEXT,
            value_integer INTEGER,
            value_real REAL,
            value_boolean INTEGER,
            provider TEXT NOT NULL,
            provider_version TEXT,
            warning TEXT,
            observed_at TEXT NOT NULL
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
            id TEXT PRIMARY KEY,
            subject_id TEXT NOT NULL,
            kind TEXT NOT NULL,
            value_type TEXT NOT NULL,
            value_text TEXT,
            value_integer INTEGER,
            value_real REAL,
            value_boolean INTEGER,
            confidence REAL NOT NULL CHECK (
                confidence >= 0.0 AND confidence <= 1.0
            ),
            rule_id TEXT NOT NULL,
            rule_version TEXT NOT NULL,
            inferred_at TEXT NOT NULL
        );

        CREATE TABLE orion_knowledge_evidence (
            knowledge_id TEXT NOT NULL,
            evidence_id TEXT NOT NULL,
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
