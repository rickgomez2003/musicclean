"""SQLite EvidenceRepository implementation."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from datetime import datetime

from musicclean.orion.domain import (
    EvidenceKind,
    EvidenceProvenance,
    EvidenceRecord,
    EvidenceValue,
)
from musicclean.orion.shared import EntityId


def _serialize_value(
    value: EvidenceValue,
) -> tuple[str, str | None, int | None, float | None, int | None]:
    if isinstance(value, bool):
        return ("bool", None, None, None, int(value))
    if isinstance(value, int):
        return ("int", None, value, None, None)
    if isinstance(value, float):
        return ("float", None, None, value, None)
    return ("str", value, None, None, None)


def _deserialize_value(row: sqlite3.Row) -> EvidenceValue:
    value_type = str(row["value_type"])
    if value_type == "bool":
        return bool(row["value_boolean"])
    if value_type == "int":
        return int(row["value_integer"])
    if value_type == "float":
        return float(row["value_real"])
    return str(row["value_text"])


class SqliteEvidenceRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def save(self, evidence: EvidenceRecord) -> None:
        value_type, text, integer, real, boolean = _serialize_value(evidence.value)
        self._connection.execute(
            """
            INSERT INTO orion_evidence(
                id, subject_id, kind, value_type, value_text, value_integer,
                value_real, value_boolean, provider, provider_version, warning,
                observed_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(evidence.id),
                str(evidence.subject_id),
                evidence.kind.value,
                value_type,
                text,
                integer,
                real,
                boolean,
                evidence.provenance.provider,
                evidence.provenance.provider_version,
                evidence.provenance.warning,
                evidence.provenance.observed_at.isoformat(),
            ),
        )

    def save_many(self, evidence: Iterable[EvidenceRecord]) -> None:
        for record in evidence:
            self.save(record)

    def list_for_subject(self, subject_id: EntityId) -> tuple[EvidenceRecord, ...]:
        rows = self._connection.execute(
            """
            SELECT * FROM orion_evidence
             WHERE subject_id = ?
             ORDER BY observed_at, kind, id
            """,
            (str(subject_id),),
        ).fetchall()
        return tuple(
            EvidenceRecord(
                id=EntityId.parse(str(row["id"])),
                subject_id=EntityId.parse(str(row["subject_id"])),
                kind=EvidenceKind(str(row["kind"])),
                value=_deserialize_value(row),
                provenance=EvidenceProvenance(
                    provider=str(row["provider"]),
                    provider_version=(
                        str(row["provider_version"])
                        if row["provider_version"] is not None
                        else None
                    ),
                    warning=str(row["warning"]) if row["warning"] is not None else None,
                    observed_at=datetime.fromisoformat(str(row["observed_at"])),
                ),
            )
            for row in rows
        )
