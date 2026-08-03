"""SQLite ReconciliationRepository implementation."""

from __future__ import annotations

import sqlite3
from datetime import datetime

from musicclean.orion.domain import (
    ReconciliationAction,
    ReconciliationFinding,
    ReconciliationStatus,
)
from musicclean.orion.shared import EntityId


class SqliteReconciliationRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    @staticmethod
    def _from_row(row: sqlite3.Row) -> ReconciliationFinding:
        return ReconciliationFinding(
            id=EntityId.parse(str(row["id"])),
            action_plan_id=EntityId.parse(str(row["action_plan_id"])),
            status=ReconciliationStatus(str(row["status"])),
            proposed_action=ReconciliationAction(str(row["proposed_action"])),
            source_exists=bool(row["source_exists"]),
            target_exists=bool(row["target_exists"]),
            has_quarantine_audit=bool(row["has_quarantine_audit"]),
            has_restore_audit=bool(row["has_restore_audit"]),
            detail=str(row["detail"]),
            checked_at=datetime.fromisoformat(str(row["checked_at"])),
        )

    def get(self, finding_id: EntityId) -> ReconciliationFinding | None:
        row = self._connection.execute(
            "SELECT * FROM orion_reconciliation_findings WHERE id = ?",
            (str(finding_id),),
        ).fetchone()
        return None if row is None else self._from_row(row)

    def save(self, finding: ReconciliationFinding) -> None:
        self._connection.execute(
            """
            INSERT INTO orion_reconciliation_findings(
                id, action_plan_id, status, proposed_action, source_exists,
                target_exists, has_quarantine_audit, has_restore_audit,
                detail, checked_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(finding.id),
                str(finding.action_plan_id),
                finding.status.value,
                finding.proposed_action.value,
                int(finding.source_exists),
                int(finding.target_exists),
                int(finding.has_quarantine_audit),
                int(finding.has_restore_audit),
                finding.detail,
                finding.checked_at.isoformat(),
            ),
        )

    def list_for_plan(self, plan_id: EntityId) -> tuple[ReconciliationFinding, ...]:
        rows = self._connection.execute(
            """
            SELECT * FROM orion_reconciliation_findings
             WHERE action_plan_id = ?
             ORDER BY checked_at, id
            """,
            (str(plan_id),),
        ).fetchall()
        return tuple(self._from_row(row) for row in rows)
