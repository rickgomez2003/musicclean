"""SQLite repositories for review, authorization, and action planning."""

from __future__ import annotations

import sqlite3
from datetime import datetime

from musicclean.orion.domain import (
    ActionPlan,
    AuthorizationGrant,
    DecisionReview,
    PlannedAction,
    ReviewOutcome,
)
from musicclean.orion.shared import EntityId


class SqliteReviewRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def save(self, review: DecisionReview) -> None:
        self._connection.execute(
            """
            INSERT INTO orion_decision_reviews(
                id, decision_id, outcome, reviewed_by, reviewed_at, note
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                str(review.id),
                str(review.decision_id),
                review.outcome.value,
                review.reviewed_by,
                review.reviewed_at.isoformat(),
                review.note,
            ),
        )

    def latest_for_decision(self, decision_id: EntityId) -> DecisionReview | None:
        row = self._connection.execute(
            """
            SELECT * FROM orion_decision_reviews
             WHERE decision_id = ?
             ORDER BY reviewed_at DESC, id DESC
             LIMIT 1
            """,
            (str(decision_id),),
        ).fetchone()
        if row is None:
            return None
        return DecisionReview(
            id=EntityId.parse(str(row["id"])),
            decision_id=EntityId.parse(str(row["decision_id"])),
            outcome=ReviewOutcome(str(row["outcome"])),
            reviewed_by=str(row["reviewed_by"]),
            reviewed_at=datetime.fromisoformat(str(row["reviewed_at"])),
            note=str(row["note"]) if row["note"] is not None else None,
        )


class SqliteAuthorizationRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    @staticmethod
    def _from_row(row: sqlite3.Row) -> AuthorizationGrant:
        return AuthorizationGrant(
            id=EntityId.parse(str(row["id"])),
            decision_id=EntityId.parse(str(row["decision_id"])),
            review_id=EntityId.parse(str(row["review_id"])),
            granted_by=str(row["granted_by"]),
            granted_at=datetime.fromisoformat(str(row["granted_at"])),
        )

    def get(self, authorization_id: EntityId) -> AuthorizationGrant | None:
        row = self._connection.execute(
            "SELECT * FROM orion_authorizations WHERE id = ?",
            (str(authorization_id),),
        ).fetchone()
        return None if row is None else self._from_row(row)

    def save(self, grant: AuthorizationGrant) -> None:
        self._connection.execute(
            """
            INSERT INTO orion_authorizations(
                id, decision_id, review_id, granted_by, granted_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                str(grant.id),
                str(grant.decision_id),
                str(grant.review_id),
                grant.granted_by,
                grant.granted_at.isoformat(),
            ),
        )

    def latest_for_decision(
        self,
        decision_id: EntityId,
    ) -> AuthorizationGrant | None:
        row = self._connection.execute(
            """
            SELECT * FROM orion_authorizations
             WHERE decision_id = ?
             ORDER BY granted_at DESC, id DESC
             LIMIT 1
            """,
            (str(decision_id),),
        ).fetchone()
        return None if row is None else self._from_row(row)


class SqliteActionPlanRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    @staticmethod
    def _from_row(row: sqlite3.Row) -> ActionPlan:
        return ActionPlan(
            id=EntityId.parse(str(row["id"])),
            decision_id=EntityId.parse(str(row["decision_id"])),
            authorization_id=EntityId.parse(str(row["authorization_id"])),
            action=PlannedAction(str(row["action"])),
            source_location=str(row["source_location"]),
            target_location=str(row["target_location"]),
            created_at=datetime.fromisoformat(str(row["created_at"])),
        )

    def save(self, plan: ActionPlan) -> None:
        self._connection.execute(
            """
            INSERT INTO orion_action_plans(
                id, decision_id, authorization_id, action, source_location,
                target_location, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(plan.id),
                str(plan.decision_id),
                str(plan.authorization_id),
                plan.action.value,
                plan.source_location,
                plan.target_location,
                plan.created_at.isoformat(),
            ),
        )

    def get(self, plan_id: EntityId) -> ActionPlan | None:
        row = self._connection.execute(
            "SELECT * FROM orion_action_plans WHERE id = ?",
            (str(plan_id),),
        ).fetchone()
        return None if row is None else self._from_row(row)

    def list_for_decision(self, decision_id: EntityId) -> tuple[ActionPlan, ...]:
        rows = self._connection.execute(
            """
            SELECT * FROM orion_action_plans
             WHERE decision_id = ?
             ORDER BY created_at, id
            """,
            (str(decision_id),),
        ).fetchall()
        return tuple(self._from_row(row) for row in rows)

    def list_all(self) -> tuple[ActionPlan, ...]:
        rows = self._connection.execute(
            "SELECT * FROM orion_action_plans ORDER BY created_at, id"
        ).fetchall()
        return tuple(self._from_row(row) for row in rows)
