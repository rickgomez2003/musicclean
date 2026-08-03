"""Detect and persist filesystem/database reconciliation findings."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from musicclean.orion.application.errors import NotFoundError
from musicclean.orion.domain import (
    ExecutionKind,
    ReconciliationAction,
    ReconciliationFinding,
    ReconciliationStatus,
)
from musicclean.orion.ports import FilesystemMutator, UnitOfWorkFactory
from musicclean.orion.shared import Clock, EntityId


@dataclass(frozen=True, slots=True)
class ReconcileActionPlan:
    """Command for reconciling one persisted ActionPlan."""

    action_plan_id: EntityId


def reconcile_action_plan(
    command: ReconcileActionPlan,
    filesystem: FilesystemMutator,
    clock: Clock,
    uow_factory: UnitOfWorkFactory,
) -> ReconciliationFinding:
    """Classify filesystem/audit state without mutating the filesystem."""
    with uow_factory() as uow:
        plan = uow.action_plans.get(command.action_plan_id)
        if plan is None:
            raise NotFoundError(f"action plan not found: {command.action_plan_id}")

        source_exists = filesystem.exists(plan.source_location)
        target_exists = filesystem.exists(plan.target_location)
        quarantine = uow.executions.latest_for_plan_kind(
            plan.id,
            ExecutionKind.QUARANTINE,
        )
        restore = uow.executions.latest_for_plan_kind(
            plan.id,
            ExecutionKind.RESTORE,
        )

        finding = classify_reconciliation(
            action_plan_id=plan.id,
            source_exists=source_exists,
            target_exists=target_exists,
            has_quarantine_audit=quarantine is not None,
            has_restore_audit=restore is not None,
            checked_at=clock.now(),
        )
        uow.reconciliations.save(finding)
        uow.commit()
        return finding


def classify_reconciliation(
    *,
    action_plan_id: EntityId,
    source_exists: bool,
    target_exists: bool,
    has_quarantine_audit: bool,
    has_restore_audit: bool,
    checked_at: datetime,
) -> ReconciliationFinding:
    """Pure classification for recovery and operator review."""
    if source_exists and target_exists:
        return _finding(
            action_plan_id,
            ReconciliationStatus.AMBIGUOUS_BOTH_EXIST,
            ReconciliationAction.REVIEW,
            source_exists,
            target_exists,
            has_quarantine_audit,
            has_restore_audit,
            "Both active and quarantine locations exist; automatic repair is unsafe.",
            checked_at,
        )

    if not source_exists and not target_exists:
        return _finding(
            action_plan_id,
            ReconciliationStatus.MISSING_BOTH,
            ReconciliationAction.REVIEW,
            source_exists,
            target_exists,
            has_quarantine_audit,
            has_restore_audit,
            "Neither active nor quarantine location exists; manual review is required.",
            checked_at,
        )

    if target_exists and not source_exists:
        if has_quarantine_audit and not has_restore_audit:
            status = ReconciliationStatus.CONSISTENT_QUARANTINED
            action = ReconciliationAction.NONE
            detail = "File is quarantined and the quarantine audit is present."
        elif not has_quarantine_audit:
            status = ReconciliationStatus.AUDIT_MISSING_AFTER_QUARANTINE
            action = ReconciliationAction.RECOVER_QUARANTINE_AUDIT
            detail = "Filesystem indicates quarantine completed but its audit is missing."
        else:
            status = ReconciliationStatus.AMBIGUOUS_BOTH_EXIST
            action = ReconciliationAction.REVIEW
            detail = "Quarantine location exists but audit history is contradictory."
        return _finding(
            action_plan_id,
            status,
            action,
            source_exists,
            target_exists,
            has_quarantine_audit,
            has_restore_audit,
            detail,
            checked_at,
        )

    # source exists and target does not
    if has_restore_audit:
        status = ReconciliationStatus.CONSISTENT_RESTORED
        action = ReconciliationAction.NONE
        detail = "File is active and a restore audit is present."
    elif has_quarantine_audit:
        status = ReconciliationStatus.AUDIT_MISSING_AFTER_RESTORE
        action = ReconciliationAction.RECOVER_RESTORE_AUDIT
        detail = "Filesystem indicates restore completed but its audit is missing."
    else:
        status = ReconciliationStatus.CONSISTENT_ACTIVE
        action = ReconciliationAction.NONE
        detail = "File remains active and no execution audit exists."

    return _finding(
        action_plan_id,
        status,
        action,
        source_exists,
        target_exists,
        has_quarantine_audit,
        has_restore_audit,
        detail,
        checked_at,
    )


def _finding(
    action_plan_id: EntityId,
    status: ReconciliationStatus,
    proposed_action: ReconciliationAction,
    source_exists: bool,
    target_exists: bool,
    has_quarantine_audit: bool,
    has_restore_audit: bool,
    detail: str,
    checked_at: datetime,
) -> ReconciliationFinding:
    return ReconciliationFinding(
        action_plan_id=action_plan_id,
        status=status,
        proposed_action=proposed_action,
        source_exists=source_exists,
        target_exists=target_exists,
        has_quarantine_audit=has_quarantine_audit,
        has_restore_audit=has_restore_audit,
        detail=detail,
        checked_at=checked_at,
    )
