"""SQLite ExecutionRepository implementation."""

from __future__ import annotations

import sqlite3
from datetime import datetime

from musicclean.orion.domain import ExecutionKind, ExecutionRecord
from musicclean.orion.shared import EntityId


class SqliteExecutionRepository:
    """Append-only repository for completed filesystem operations."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    @staticmethod
    def _from_row(row: sqlite3.Row) -> ExecutionRecord:
        return ExecutionRecord(
            id=EntityId.parse(str(row["id"])),
            action_plan_id=EntityId.parse(str(row["action_plan_id"])),
            kind=ExecutionKind(str(row["kind"])),
            source_location=str(row["source_location"]),
            target_location=str(row["target_location"]),
            executed_by=str(row["executed_by"]),
            executed_at=datetime.fromisoformat(str(row["executed_at"])),
        )

    def save(self, execution: ExecutionRecord) -> None:
        self._connection.execute(
            """
            INSERT INTO orion_executions(
                id, action_plan_id, kind, source_location, target_location,
                executed_by, executed_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(execution.id),
                str(execution.action_plan_id),
                execution.kind.value,
                execution.source_location,
                execution.target_location,
                execution.executed_by,
                execution.executed_at.isoformat(),
            ),
        )

    def list_for_plan(self, plan_id: EntityId) -> tuple[ExecutionRecord, ...]:
        rows = self._connection.execute(
            """
            SELECT * FROM orion_executions
             WHERE action_plan_id = ?
             ORDER BY executed_at, id
            """,
            (str(plan_id),),
        ).fetchall()
        return tuple(self._from_row(row) for row in rows)

    def latest_for_plan_kind(
        self,
        plan_id: EntityId,
        kind: ExecutionKind,
    ) -> ExecutionRecord | None:
        row = self._connection.execute(
            """
            SELECT * FROM orion_executions
             WHERE action_plan_id = ? AND kind = ?
             ORDER BY executed_at DESC, id DESC
             LIMIT 1
            """,
            (str(plan_id), kind.value),
        ).fetchone()
        return None if row is None else self._from_row(row)
