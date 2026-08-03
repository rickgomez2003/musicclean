"""Operational hardening services for idempotency, leases, and startup recovery."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from musicclean.orion.application.errors import ConflictError
from musicclean.orion.application.reconcile_execution import (
    ReconcileActionPlan,
    reconcile_action_plan,
)
from musicclean.orion.domain import (
    ActionPlanLease,
    IdempotencyRecord,
    IdempotencyStatus,
    ReconciliationFinding,
)
from musicclean.orion.ports import FilesystemMutator, UnitOfWorkFactory
from musicclean.orion.shared import Clock, EntityId


@dataclass(frozen=True, slots=True)
class BeginIdempotentOperation:
    key: str
    operation: str
    subject_id: EntityId


def begin_idempotent_operation(
    command: BeginIdempotentOperation,
    clock: Clock,
    uow_factory: UnitOfWorkFactory,
) -> IdempotencyRecord:
    with uow_factory() as uow:
        existing = uow.idempotency.get(command.key)
        if existing is not None:
            return existing

        record = IdempotencyRecord(
            key=command.key,
            operation=command.operation,
            subject_id=command.subject_id,
            status=IdempotencyStatus.STARTED,
            created_at=clock.now(),
        )
        uow.idempotency.save(record)
        uow.commit()
        return record


def complete_idempotent_operation(
    key: str,
    clock: Clock,
    uow_factory: UnitOfWorkFactory,
) -> None:
    with uow_factory() as uow:
        record = uow.idempotency.get(key)
        if record is None:
            raise ConflictError(f"idempotency key not found: {key}")
        if record.status is IdempotencyStatus.COMPLETED:
            return
        uow.idempotency.complete(key, clock.now())
        uow.commit()


@dataclass(frozen=True, slots=True)
class AcquirePlanLease:
    action_plan_id: EntityId
    owner: str
    ttl_seconds: int = 60


def acquire_plan_lease(
    command: AcquirePlanLease,
    clock: Clock,
    uow_factory: UnitOfWorkFactory,
) -> ActionPlanLease:
    if command.ttl_seconds <= 0:
        raise ValueError("ttl_seconds must be positive")

    now = clock.now()
    with uow_factory() as uow:
        existing = uow.leases.get_for_plan(command.action_plan_id)
        if existing is not None and existing.is_active_at(now):
            if existing.owner == command.owner:
                return existing
            raise ConflictError(f"action plan is leased by another owner: {existing.owner}")

        lease = ActionPlanLease(
            action_plan_id=command.action_plan_id,
            owner=command.owner,
            acquired_at=now,
            expires_at=now + timedelta(seconds=command.ttl_seconds),
        )
        uow.leases.acquire(lease)
        uow.commit()
        return lease


def release_plan_lease(
    action_plan_id: EntityId,
    owner: str,
    uow_factory: UnitOfWorkFactory,
) -> None:
    with uow_factory() as uow:
        existing = uow.leases.get_for_plan(action_plan_id)
        if existing is None:
            return
        if existing.owner != owner:
            raise ConflictError("only the lease owner may release an active lease")
        uow.leases.release(action_plan_id, owner)
        uow.commit()


@dataclass(frozen=True, slots=True)
class StartupRecoverySweep:
    """Reconcile every persisted ActionPlan without mutating files."""


def startup_recovery_sweep(
    command: StartupRecoverySweep,
    filesystem: FilesystemMutator,
    clock: Clock,
    uow_factory: UnitOfWorkFactory,
) -> tuple[ReconciliationFinding, ...]:
    del command
    with uow_factory() as uow:
        plans = uow.action_plans.list_all()

    findings: list[ReconciliationFinding] = []
    for plan in plans:
        findings.append(
            reconcile_action_plan(
                ReconcileActionPlan(plan.id),
                filesystem,
                clock,
                uow_factory,
            )
        )
    return tuple(findings)
