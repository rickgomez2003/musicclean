"""Safe review, authorization, and quarantine-planning use cases."""

from __future__ import annotations

from dataclasses import dataclass

from musicclean.orion.application.errors import ConflictError, NotFoundError
from musicclean.orion.domain import (
    ActionPlan,
    AuthorizationGrant,
    DecisionAction,
    DecisionReview,
    PlannedAction,
    ReviewOutcome,
    UndoDescriptor,
)
from musicclean.orion.ports import UnitOfWorkFactory
from musicclean.orion.shared import Clock, EntityId


@dataclass(frozen=True, slots=True)
class ReviewDecision:
    decision_id: EntityId
    outcome: ReviewOutcome
    reviewed_by: str
    note: str | None = None


def review_decision(
    command: ReviewDecision,
    clock: Clock,
    uow_factory: UnitOfWorkFactory,
) -> DecisionReview:
    with uow_factory() as uow:
        if uow.decisions.get(command.decision_id) is None:
            raise NotFoundError(f"decision not found: {command.decision_id}")

        review = DecisionReview(
            decision_id=command.decision_id,
            outcome=command.outcome,
            reviewed_by=command.reviewed_by,
            reviewed_at=clock.now(),
            note=command.note,
        )
        uow.reviews.save(review)
        uow.commit()
        return review


@dataclass(frozen=True, slots=True)
class AuthorizeDecision:
    decision_id: EntityId
    granted_by: str


def authorize_decision(
    command: AuthorizeDecision,
    clock: Clock,
    uow_factory: UnitOfWorkFactory,
) -> AuthorizationGrant:
    with uow_factory() as uow:
        decision = uow.decisions.get(command.decision_id)
        if decision is None:
            raise NotFoundError(f"decision not found: {command.decision_id}")

        review = uow.reviews.latest_for_decision(command.decision_id)
        if review is None or review.outcome is not ReviewOutcome.APPROVED:
            raise ConflictError("decision must have an approved review before authorization")

        grant = AuthorizationGrant(
            decision_id=decision.id,
            review_id=review.id,
            granted_by=command.granted_by,
            granted_at=clock.now(),
        )
        uow.authorizations.save(grant)
        uow.commit()
        return grant


@dataclass(frozen=True, slots=True)
class PlanQuarantine:
    decision_id: EntityId
    source_location: str
    quarantine_location: str


@dataclass(frozen=True, slots=True)
class PlannedQuarantine:
    plan: ActionPlan
    undo: UndoDescriptor


def plan_quarantine(
    command: PlanQuarantine,
    clock: Clock,
    uow_factory: UnitOfWorkFactory,
) -> PlannedQuarantine:
    with uow_factory() as uow:
        decision = uow.decisions.get(command.decision_id)
        if decision is None:
            raise NotFoundError(f"decision not found: {command.decision_id}")

        if decision.action not in {
            DecisionAction.REVIEW,
            DecisionAction.REPAIR_METADATA,
            DecisionAction.REANALYZE,
        }:
            raise ConflictError(
                f"decision action {decision.action.value} is not eligible for quarantine planning"
            )

        authorization = uow.authorizations.latest_for_decision(command.decision_id)
        if authorization is None:
            raise ConflictError("decision must be explicitly authorized before planning")

        plan = ActionPlan(
            decision_id=decision.id,
            authorization_id=authorization.id,
            action=PlannedAction.QUARANTINE,
            source_location=command.source_location,
            target_location=command.quarantine_location,
            created_at=clock.now(),
        )
        undo = UndoDescriptor(
            action_plan_id=plan.id,
            restore_from=plan.target_location,
            restore_to=plan.source_location,
        )
        uow.action_plans.save(plan)
        uow.commit()
        return PlannedQuarantine(plan=plan, undo=undo)
