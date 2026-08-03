"""SQLite KnowledgeRepository implementation."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from datetime import datetime

from musicclean.orion.domain import KnowledgeFact, KnowledgeKind, KnowledgeValue
from musicclean.orion.shared import Confidence, EntityId


def _serialize_value(
    value: KnowledgeValue,
) -> tuple[str, str | None, int | None, float | None, int | None]:
    if isinstance(value, bool):
        return ("bool", None, None, None, int(value))
    if isinstance(value, int):
        return ("int", None, value, None, None)
    if isinstance(value, float):
        return ("float", None, None, value, None)
    return ("str", value, None, None, None)


def _deserialize_value(row: sqlite3.Row) -> KnowledgeValue:
    value_type = str(row["value_type"])
    if value_type == "bool":
        return bool(row["value_boolean"])
    if value_type == "int":
        return int(row["value_integer"])
    if value_type == "float":
        return float(row["value_real"])
    return str(row["value_text"])


class SqliteKnowledgeRepository:
    """Append-oriented SQLite repository for Knowledge facts."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def save(self, fact: KnowledgeFact) -> None:
        value_type, text, integer, real, boolean = _serialize_value(fact.value)
        self._connection.execute(
            """
            INSERT INTO orion_knowledge(
                id, subject_id, kind, value_type, value_text, value_integer,
                value_real, value_boolean, confidence, rule_id, rule_version,
                inferred_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(fact.id),
                str(fact.subject_id),
                fact.kind.value,
                value_type,
                text,
                integer,
                real,
                boolean,
                fact.confidence.value,
                fact.rule_id,
                fact.rule_version,
                fact.inferred_at.isoformat(),
            ),
        )
        for ordinal, evidence_id in enumerate(fact.evidence_ids):
            self._connection.execute(
                """
                INSERT INTO orion_knowledge_evidence(
                    knowledge_id, evidence_id, ordinal
                )
                VALUES (?, ?, ?)
                """,
                (str(fact.id), str(evidence_id), ordinal),
            )

    def save_many(self, facts: Iterable[KnowledgeFact]) -> None:
        for fact in facts:
            self.save(fact)

    def list_for_subject(self, subject_id: EntityId) -> tuple[KnowledgeFact, ...]:
        rows = self._connection.execute(
            """
            SELECT * FROM orion_knowledge
             WHERE subject_id = ?
             ORDER BY inferred_at, kind, id
            """,
            (str(subject_id),),
        ).fetchall()

        facts: list[KnowledgeFact] = []
        for row in rows:
            evidence_rows = self._connection.execute(
                """
                SELECT evidence_id
                  FROM orion_knowledge_evidence
                 WHERE knowledge_id = ?
                 ORDER BY ordinal
                """,
                (str(row["id"]),),
            ).fetchall()
            facts.append(
                KnowledgeFact(
                    id=EntityId.parse(str(row["id"])),
                    subject_id=EntityId.parse(str(row["subject_id"])),
                    kind=KnowledgeKind(str(row["kind"])),
                    value=_deserialize_value(row),
                    confidence=Confidence(float(row["confidence"])),
                    evidence_ids=tuple(
                        EntityId.parse(str(evidence_row["evidence_id"]))
                        for evidence_row in evidence_rows
                    ),
                    rule_id=str(row["rule_id"]),
                    rule_version=str(row["rule_version"]),
                    inferred_at=datetime.fromisoformat(str(row["inferred_at"])),
                )
            )
        return tuple(facts)
