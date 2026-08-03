"""SQLite repositories for approved reconciliation recovery."""

from __future__ import annotations

import sqlite3
from datetime import datetime

from musicclean.orion.domain import (
    RecoveryApproval,
    RecoveryKind,
    RecoveryRecord,
)
from musicclean.orion.shared import EntityId


class SqliteRecoveryApprovalRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    @staticmethod
    def _from_row(row: sqlite3.Row) -> RecoveryApproval:
        return RecoveryApproval(
            id=EntityId.parse(str(row["id"])),
            finding_id=EntityId.parse(str(row["finding_id"])),
            kind=RecoveryKind(str(row["kind"])),
            approved_by=str(row["approved_by"]),
            approved_at=datetime.fromisoformat(str(row["approved_at"])),
            note=str(row["note"]) if row["note"] is not None else None,
        )

    def get(self, approval_id: EntityId) -> RecoveryApproval | None:
        row = self._connection.execute(
            "SELECT * FROM orion_recovery_approvals WHERE id = ?",
            (str(approval_id),),
        ).fetchone()
        return None if row is None else self._from_row(row)

    def save(self, approval: RecoveryApproval) -> None:
        self._connection.execute(
            """
            INSERT INTO orion_recovery_approvals(
                id, finding_id, kind, approved_by, approved_at, note
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                str(approval.id),
                str(approval.finding_id),
                approval.kind.value,
                approval.approved_by,
                approval.approved_at.isoformat(),
                approval.note,
            ),
        )


class SqliteRecoveryRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    @staticmethod
    def _from_row(row: sqlite3.Row) -> RecoveryRecord:
        return RecoveryRecord(
            id=EntityId.parse(str(row["id"])),
            finding_id=EntityId.parse(str(row["finding_id"])),
            approval_id=EntityId.parse(str(row["approval_id"])),
            execution_id=EntityId.parse(str(row["execution_id"])),
            kind=RecoveryKind(str(row["kind"])),
            recovered_by=str(row["recovered_by"]),
            recovered_at=datetime.fromisoformat(str(row["recovered_at"])),
        )

    def save(self, recovery: RecoveryRecord) -> None:
        self._connection.execute(
            """
            INSERT INTO orion_recovery_records(
                id, finding_id, approval_id, execution_id, kind,
                recovered_by, recovered_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(recovery.id),
                str(recovery.finding_id),
                str(recovery.approval_id),
                str(recovery.execution_id),
                recovery.kind.value,
                recovery.recovered_by,
                recovery.recovered_at.isoformat(),
            ),
        )

    def get_by_approval(self, approval_id: EntityId) -> RecoveryRecord | None:
        row = self._connection.execute(
            "SELECT * FROM orion_recovery_records WHERE approval_id = ?",
            (str(approval_id),),
        ).fetchone()
        return None if row is None else self._from_row(row)

    def list_for_finding(self, finding_id: EntityId) -> tuple[RecoveryRecord, ...]:
        rows = self._connection.execute(
            """
            SELECT * FROM orion_recovery_records
             WHERE finding_id = ?
             ORDER BY recovered_at, id
            """,
            (str(finding_id),),
        ).fetchall()
        return tuple(self._from_row(row) for row in rows)
