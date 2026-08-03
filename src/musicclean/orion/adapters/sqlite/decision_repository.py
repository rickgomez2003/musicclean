"""SQLite DecisionRepository implementation."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from datetime import datetime

from musicclean.orion.domain import Decision, DecisionAction
from musicclean.orion.shared import Confidence, EntityId


class SqliteDecisionRepository:
    """Append-oriented SQLite repository for recommendations."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def save(self, decision: Decision) -> None:
        self._connection.execute(
            """
            INSERT INTO orion_decisions(
                id, subject_id, action, confidence, rationale, rule_id,
                rule_version, decided_at, risk
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(decision.id),
                str(decision.subject_id),
                decision.action.value,
                decision.confidence.value,
                decision.rationale,
                decision.rule_id,
                decision.rule_version,
                decision.decided_at.isoformat(),
                decision.risk,
            ),
        )
        for ordinal, knowledge_id in enumerate(decision.knowledge_ids):
            self._connection.execute(
                """
                INSERT INTO orion_decision_knowledge(
                    decision_id, knowledge_id, ordinal
                )
                VALUES (?, ?, ?)
                """,
                (str(decision.id), str(knowledge_id), ordinal),
            )

    def save_many(self, decisions: Iterable[Decision]) -> None:
        for decision in decisions:
            self.save(decision)

    def list_for_subject(self, subject_id: EntityId) -> tuple[Decision, ...]:
        rows = self._connection.execute(
            """
            SELECT * FROM orion_decisions
             WHERE subject_id = ?
             ORDER BY decided_at, action, id
            """,
            (str(subject_id),),
        ).fetchall()

        decisions: list[Decision] = []
        for row in rows:
            knowledge_rows = self._connection.execute(
                """
                SELECT knowledge_id
                  FROM orion_decision_knowledge
                 WHERE decision_id = ?
                 ORDER BY ordinal
                """,
                (str(row["id"]),),
            ).fetchall()
            decisions.append(
                Decision(
                    id=EntityId.parse(str(row["id"])),
                    subject_id=EntityId.parse(str(row["subject_id"])),
                    action=DecisionAction(str(row["action"])),
                    confidence=Confidence(float(row["confidence"])),
                    rationale=str(row["rationale"]),
                    knowledge_ids=tuple(
                        EntityId.parse(str(item["knowledge_id"])) for item in knowledge_rows
                    ),
                    rule_id=str(row["rule_id"]),
                    rule_version=str(row["rule_version"]),
                    decided_at=datetime.fromisoformat(str(row["decided_at"])),
                    risk=str(row["risk"]) if row["risk"] is not None else None,
                )
            )
        return tuple(decisions)
