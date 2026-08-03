"""Coordinated, idempotent execution paths."""

from __future__ import annotations

from dataclasses import dataclass

from musicclean.orion.application.errors import ConflictError
from musicclean.orion.application.operational_hardening import (
    AcquirePlanLease,
    BeginIdempotentOperation,
    acquire_plan_lease,
    begin_idempotent_operation,
    complete_idempotent_operation,
    release_plan_lease,
)
from musicclean.orion.application.recovery_actions import (
    ApplyRecovery,
    apply_recovery,
)
from musicclean.orion.application.safe_executor import (
    ExecuteQuarantine,
    RestoreQuarantine,
    execute_quarantine,
    restore_quarantine,
)
from musicclean.orion.domain import (
    ExecutionKind,
    ExecutionRecord,
    IdempotencyStatus,
    RecoveryRecord,
)
from musicclean.orion.ports import FilesystemMutator, UnitOfWorkFactory
from musicclean.orion.shared import Clock, EntityId


@dataclass(frozen=True, slots=True)
class CoordinatedExecution:
    action_plan_id: EntityId
    operator: str
    idempotency_key: str
    lease_owner: str
    lease_ttl_seconds: int = 60


def execute_quarantine_coordinated(
    command: CoordinatedExecution,
    filesystem: FilesystemMutator,
    clock: Clock,
    uow_factory: UnitOfWorkFactory,
) -> ExecutionRecord:
    operation = "execute-quarantine"
    record = begin_idempotent_operation(
        BeginIdempotentOperation(
            key=command.idempotency_key,
            operation=operation,
            subject_id=command.action_plan_id,
        ),
        clock,
        uow_factory,
    )
    if record.status is IdempotencyStatus.COMPLETED:
        with uow_factory() as uow:
            existing = uow.executions.latest_for_plan_kind(
                command.action_plan_id,
                ExecutionKind.QUARANTINE,
            )
        if existing is None:
            raise ConflictError("idempotency record is completed but quarantine result is missing")
        return existing

    acquire_plan_lease(
        AcquirePlanLease(
            command.action_plan_id,
            command.lease_owner,
            command.lease_ttl_seconds,
        ),
        clock,
        uow_factory,
    )
    try:
        result = execute_quarantine(
            ExecuteQuarantine(command.action_plan_id, command.operator),
            filesystem,
            clock,
            uow_factory,
        )
        complete_idempotent_operation(
            command.idempotency_key,
            clock,
            uow_factory,
        )
        return result
    finally:
        release_plan_lease(
            command.action_plan_id,
            command.lease_owner,
            uow_factory,
        )


def restore_quarantine_coordinated(
    command: CoordinatedExecution,
    filesystem: FilesystemMutator,
    clock: Clock,
    uow_factory: UnitOfWorkFactory,
) -> ExecutionRecord:
    operation = "restore-quarantine"
    record = begin_idempotent_operation(
        BeginIdempotentOperation(
            key=command.idempotency_key,
            operation=operation,
            subject_id=command.action_plan_id,
        ),
        clock,
        uow_factory,
    )
    if record.status is IdempotencyStatus.COMPLETED:
        with uow_factory() as uow:
            existing = uow.executions.latest_for_plan_kind(
                command.action_plan_id,
                ExecutionKind.RESTORE,
            )
        if existing is None:
            raise ConflictError("idempotency record is completed but restore result is missing")
        return existing

    acquire_plan_lease(
        AcquirePlanLease(
            command.action_plan_id,
            command.lease_owner,
            command.lease_ttl_seconds,
        ),
        clock,
        uow_factory,
    )
    try:
        result = restore_quarantine(
            RestoreQuarantine(command.action_plan_id, command.operator),
            filesystem,
            clock,
            uow_factory,
        )
        complete_idempotent_operation(
            command.idempotency_key,
            clock,
            uow_factory,
        )
        return result
    finally:
        release_plan_lease(
            command.action_plan_id,
            command.lease_owner,
            uow_factory,
        )


@dataclass(frozen=True, slots=True)
class CoordinatedRecovery:
    approval_id: EntityId
    operator: str
    idempotency_key: str
    action_plan_id: EntityId
    lease_owner: str
    lease_ttl_seconds: int = 60


def apply_recovery_coordinated(
    command: CoordinatedRecovery,
    filesystem: FilesystemMutator,
    clock: Clock,
    uow_factory: UnitOfWorkFactory,
) -> RecoveryRecord:
    operation = "apply-recovery"
    record = begin_idempotent_operation(
        BeginIdempotentOperation(
            key=command.idempotency_key,
            operation=operation,
            subject_id=command.approval_id,
        ),
        clock,
        uow_factory,
    )
    if record.status is IdempotencyStatus.COMPLETED:
        with uow_factory() as uow:
            existing = uow.recoveries.get_by_approval(command.approval_id)
        if existing is None:
            raise ConflictError("idempotency record is completed but recovery result is missing")
        return existing

    acquire_plan_lease(
        AcquirePlanLease(
            command.action_plan_id,
            command.lease_owner,
            command.lease_ttl_seconds,
        ),
        clock,
        uow_factory,
    )
    try:
        result = apply_recovery(
            ApplyRecovery(command.approval_id, command.operator),
            filesystem,
            clock,
            uow_factory,
        )
        complete_idempotent_operation(
            command.idempotency_key,
            clock,
            uow_factory,
        )
        return result
    finally:
        release_plan_lease(
            command.action_plan_id,
            command.lease_owner,
            uow_factory,
        )
