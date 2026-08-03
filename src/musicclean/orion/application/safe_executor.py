"""Authorized quarantine execution and restore use cases."""

from __future__ import annotations

from dataclasses import dataclass

from musicclean.orion.application.errors import ConflictError, NotFoundError
from musicclean.orion.domain import ExecutionKind, ExecutionRecord, PlannedAction
from musicclean.orion.ports import FilesystemMutator, UnitOfWorkFactory
from musicclean.orion.shared import Clock, EntityId


@dataclass(frozen=True, slots=True)
class ExecuteQuarantine:
    action_plan_id: EntityId
    executed_by: str


def execute_quarantine(
    command: ExecuteQuarantine,
    filesystem: FilesystemMutator,
    clock: Clock,
    uow_factory: UnitOfWorkFactory,
) -> ExecutionRecord:
    """Execute an authorized quarantine plan with no-overwrite preconditions."""
    with uow_factory() as uow:
        plan = uow.action_plans.get(command.action_plan_id)
        if plan is None:
            raise NotFoundError(f"action plan not found: {command.action_plan_id}")
        if plan.action is not PlannedAction.QUARANTINE:
            raise ConflictError("action plan is not a quarantine plan")

        authorization = uow.authorizations.get(plan.authorization_id)
        if authorization is None:
            raise ConflictError("action plan authorization no longer exists")
        if authorization.decision_id != plan.decision_id:
            raise ConflictError("authorization does not match action plan decision")

        if uow.executions.latest_for_plan_kind(plan.id, ExecutionKind.QUARANTINE) is not None:
            raise ConflictError("quarantine plan has already been executed")

        _require_move_preconditions(
            filesystem,
            plan.source_location,
            plan.target_location,
        )

        filesystem.move(plan.source_location, plan.target_location)
        execution = ExecutionRecord(
            action_plan_id=plan.id,
            kind=ExecutionKind.QUARANTINE,
            source_location=plan.source_location,
            target_location=plan.target_location,
            executed_by=command.executed_by,
            executed_at=clock.now(),
        )

        try:
            uow.executions.save(execution)
            uow.commit()
        except Exception:
            _attempt_compensation(
                filesystem,
                source=plan.target_location,
                target=plan.source_location,
            )
            raise

        return execution


@dataclass(frozen=True, slots=True)
class RestoreQuarantine:
    action_plan_id: EntityId
    restored_by: str


def restore_quarantine(
    command: RestoreQuarantine,
    filesystem: FilesystemMutator,
    clock: Clock,
    uow_factory: UnitOfWorkFactory,
) -> ExecutionRecord:
    """Restore a previously quarantined file to its original location."""
    with uow_factory() as uow:
        plan = uow.action_plans.get(command.action_plan_id)
        if plan is None:
            raise NotFoundError(f"action plan not found: {command.action_plan_id}")

        quarantine = uow.executions.latest_for_plan_kind(
            plan.id,
            ExecutionKind.QUARANTINE,
        )
        if quarantine is None:
            raise ConflictError("quarantine plan has not been executed")

        if uow.executions.latest_for_plan_kind(plan.id, ExecutionKind.RESTORE) is not None:
            raise ConflictError("quarantine plan has already been restored")

        _require_move_preconditions(
            filesystem,
            plan.target_location,
            plan.source_location,
        )

        filesystem.move(plan.target_location, plan.source_location)
        execution = ExecutionRecord(
            action_plan_id=plan.id,
            kind=ExecutionKind.RESTORE,
            source_location=plan.target_location,
            target_location=plan.source_location,
            executed_by=command.restored_by,
            executed_at=clock.now(),
        )

        try:
            uow.executions.save(execution)
            uow.commit()
        except Exception:
            _attempt_compensation(
                filesystem,
                source=plan.source_location,
                target=plan.target_location,
            )
            raise

        return execution


def _require_move_preconditions(
    filesystem: FilesystemMutator,
    source: str,
    target: str,
) -> None:
    if not filesystem.exists(source):
        raise ConflictError(f"source does not exist: {source}")
    if filesystem.exists(target):
        raise ConflictError(f"target already exists: {target}")


def _attempt_compensation(
    filesystem: FilesystemMutator,
    source: str,
    target: str,
) -> None:
    """Best-effort compensation when persistence fails after a filesystem move."""
    if filesystem.exists(source) and not filesystem.exists(target):
        filesystem.move(source, target)
