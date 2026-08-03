"""Operator-approved repair of missing execution audit records."""

from __future__ import annotations

from dataclasses import dataclass

from musicclean.orion.application.errors import ConflictError, NotFoundError
from musicclean.orion.domain import (
    ExecutionKind,
    ExecutionOrigin,
    ExecutionRecord,
    ReconciliationAction,
    RecoveryApproval,
    RecoveryKind,
    RecoveryRecord,
)
from musicclean.orion.ports import FilesystemMutator, UnitOfWorkFactory
from musicclean.orion.shared import Clock, EntityId


@dataclass(frozen=True, slots=True)
class ApproveRecovery:
    finding_id: EntityId
    approved_by: str
    note: str | None = None


def approve_recovery(
    command: ApproveRecovery,
    clock: Clock,
    uow_factory: UnitOfWorkFactory,
) -> RecoveryApproval:
    """Approve exactly the recovery action proposed by a finding."""
    with uow_factory() as uow:
        finding = uow.reconciliations.get(command.finding_id)
        if finding is None:
            raise NotFoundError(f"reconciliation finding not found: {command.finding_id}")

        kind = _recovery_kind_for_action(finding.proposed_action)
        if kind is None:
            raise ConflictError("reconciliation finding is not eligible for automatic recovery")

        approval = RecoveryApproval(
            finding_id=finding.id,
            kind=kind,
            approved_by=command.approved_by,
            approved_at=clock.now(),
            note=command.note,
        )
        uow.recovery_approvals.save(approval)
        uow.commit()
        return approval


@dataclass(frozen=True, slots=True)
class ApplyRecovery:
    approval_id: EntityId
    recovered_by: str


def apply_recovery(
    command: ApplyRecovery,
    filesystem: FilesystemMutator,
    clock: Clock,
    uow_factory: UnitOfWorkFactory,
) -> RecoveryRecord:
    """Re-check live state and synthesize only the explicitly approved audit."""
    with uow_factory() as uow:
        approval = uow.recovery_approvals.get(command.approval_id)
        if approval is None:
            raise NotFoundError(f"recovery approval not found: {command.approval_id}")

        if uow.recoveries.get_by_approval(approval.id) is not None:
            raise ConflictError("recovery approval has already been applied")

        finding = uow.reconciliations.get(approval.finding_id)
        if finding is None:
            raise NotFoundError(f"reconciliation finding not found: {approval.finding_id}")

        expected_kind = _recovery_kind_for_action(finding.proposed_action)
        if expected_kind is None or expected_kind is not approval.kind:
            raise ConflictError("recovery approval no longer matches the finding")

        plan = uow.action_plans.get(finding.action_plan_id)
        if plan is None:
            raise NotFoundError(f"action plan not found: {finding.action_plan_id}")

        _require_recovery_preconditions(
            approval.kind,
            source_exists=filesystem.exists(plan.source_location),
            target_exists=filesystem.exists(plan.target_location),
        )

        execution_kind = (
            ExecutionKind.QUARANTINE
            if approval.kind is RecoveryKind.QUARANTINE_AUDIT
            else ExecutionKind.RESTORE
        )

        if uow.executions.latest_for_plan_kind(plan.id, execution_kind) is not None:
            raise ConflictError("execution audit already exists; recovery is no longer required")

        execution = ExecutionRecord(
            action_plan_id=plan.id,
            kind=execution_kind,
            source_location=(
                plan.source_location
                if execution_kind is ExecutionKind.QUARANTINE
                else plan.target_location
            ),
            target_location=(
                plan.target_location
                if execution_kind is ExecutionKind.QUARANTINE
                else plan.source_location
            ),
            executed_by=command.recovered_by,
            executed_at=clock.now(),
            origin=ExecutionOrigin.RECOVERED,
            recovery_finding_id=finding.id,
        )
        uow.executions.save(execution)

        recovery = RecoveryRecord(
            finding_id=finding.id,
            approval_id=approval.id,
            execution_id=execution.id,
            kind=approval.kind,
            recovered_by=command.recovered_by,
            recovered_at=clock.now(),
        )
        uow.recoveries.save(recovery)
        uow.commit()
        return recovery


def _recovery_kind_for_action(
    action: ReconciliationAction,
) -> RecoveryKind | None:
    if action is ReconciliationAction.RECOVER_QUARANTINE_AUDIT:
        return RecoveryKind.QUARANTINE_AUDIT
    if action is ReconciliationAction.RECOVER_RESTORE_AUDIT:
        return RecoveryKind.RESTORE_AUDIT
    return None


def _require_recovery_preconditions(
    kind: RecoveryKind,
    *,
    source_exists: bool,
    target_exists: bool,
) -> None:
    if kind is RecoveryKind.QUARANTINE_AUDIT:
        if source_exists or not target_exists:
            raise ConflictError("filesystem no longer matches missing-quarantine-audit state")
        return

    if not source_exists or target_exists:
        raise ConflictError("filesystem no longer matches missing-restore-audit state")
