"""SQLite repositories for idempotency and action-plan leases."""

from __future__ import annotations

import sqlite3
from datetime import datetime

from musicclean.orion.domain import (
    ActionPlanLease,
    IdempotencyRecord,
    IdempotencyStatus,
)
from musicclean.orion.shared import EntityId


class SqliteIdempotencyRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def get(self, key: str) -> IdempotencyRecord | None:
        row = self._connection.execute(
            "SELECT * FROM orion_idempotency WHERE key = ?",
            (key,),
        ).fetchone()
        if row is None:
            return None
        return IdempotencyRecord(
            key=str(row["key"]),
            operation=str(row["operation"]),
            subject_id=EntityId.parse(str(row["subject_id"])),
            status=IdempotencyStatus(str(row["status"])),
            created_at=datetime.fromisoformat(str(row["created_at"])),
            completed_at=(
                datetime.fromisoformat(str(row["completed_at"]))
                if row["completed_at"] is not None
                else None
            ),
        )

    def save(self, record: IdempotencyRecord) -> None:
        self._connection.execute(
            """
            INSERT INTO orion_idempotency(
                key, operation, subject_id, status, created_at, completed_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                record.key,
                record.operation,
                str(record.subject_id),
                record.status.value,
                record.created_at.isoformat(),
                record.completed_at.isoformat() if record.completed_at else None,
            ),
        )

    def complete(self, key: str, completed_at: datetime) -> None:
        self._connection.execute(
            """
            UPDATE orion_idempotency
               SET status = ?, completed_at = ?
             WHERE key = ?
            """,
            (
                IdempotencyStatus.COMPLETED.value,
                completed_at.isoformat(),
                key,
            ),
        )


class SqliteLeaseRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def get_for_plan(self, plan_id: EntityId) -> ActionPlanLease | None:
        row = self._connection.execute(
            "SELECT * FROM orion_action_plan_leases WHERE action_plan_id = ?",
            (str(plan_id),),
        ).fetchone()
        if row is None:
            return None
        return ActionPlanLease(
            id=EntityId.parse(str(row["id"])),
            action_plan_id=EntityId.parse(str(row["action_plan_id"])),
            owner=str(row["owner"]),
            acquired_at=datetime.fromisoformat(str(row["acquired_at"])),
            expires_at=datetime.fromisoformat(str(row["expires_at"])),
        )

    def acquire(self, lease: ActionPlanLease) -> None:
        self._connection.execute(
            """
            INSERT INTO orion_action_plan_leases(
                id, action_plan_id, owner, acquired_at, expires_at
            )
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(action_plan_id) DO UPDATE SET
                id = excluded.id,
                owner = excluded.owner,
                acquired_at = excluded.acquired_at,
                expires_at = excluded.expires_at
            """,
            (
                str(lease.id),
                str(lease.action_plan_id),
                lease.owner,
                lease.acquired_at.isoformat(),
                lease.expires_at.isoformat(),
            ),
        )

    def release(self, plan_id: EntityId, owner: str) -> None:
        self._connection.execute(
            """
            DELETE FROM orion_action_plan_leases
             WHERE action_plan_id = ? AND owner = ?
            """,
            (str(plan_id), owner),
        )
