"""Stable orchestration facade for external Orion callers."""

from __future__ import annotations

from dataclasses import dataclass

from musicclean.orion.application.coordination import (
    CoordinatedExecution,
    execute_quarantine_coordinated,
    restore_quarantine_coordinated,
)
from musicclean.orion.application.reconcile_execution import (
    ReconcileActionPlan,
    reconcile_action_plan,
)
from musicclean.orion.application.service_models import (
    ServiceExecutionResult,
    ServiceHealth,
    ServiceReconciliationResult,
)
from musicclean.orion.ports import FilesystemMutator, UnitOfWorkFactory
from musicclean.orion.shared import Clock, EntityId


@dataclass(frozen=True, slots=True)
class QuarantineRequest:
    action_plan_id: EntityId
    operator: str
    idempotency_key: str
    lease_owner: str
    lease_ttl_seconds: int = 60


@dataclass(frozen=True, slots=True)
class RestoreRequest:
    action_plan_id: EntityId
    operator: str
    idempotency_key: str
    lease_owner: str
    lease_ttl_seconds: int = 60


@dataclass(frozen=True, slots=True)
class ReconcileRequest:
    action_plan_id: EntityId


class OrionService:
    """Transport-neutral facade over Orion application orchestration."""

    def __init__(
        self,
        *,
        filesystem: FilesystemMutator,
        clock: Clock,
        uow_factory: UnitOfWorkFactory,
        schema_version: int,
    ) -> None:
        self._filesystem = filesystem
        self._clock = clock
        self._uow_factory = uow_factory
        self._schema_version = schema_version

    def health(self) -> ServiceHealth:
        return ServiceHealth(
            service="musicclean-orion",
            status="ok",
            schema_version=self._schema_version,
        )

    def quarantine(self, request: QuarantineRequest) -> ServiceExecutionResult:
        execution = execute_quarantine_coordinated(
            CoordinatedExecution(
                action_plan_id=request.action_plan_id,
                operator=request.operator,
                idempotency_key=request.idempotency_key,
                lease_owner=request.lease_owner,
                lease_ttl_seconds=request.lease_ttl_seconds,
            ),
            self._filesystem,
            self._clock,
            self._uow_factory,
        )
        return ServiceExecutionResult(
            execution_id=execution.id,
            action_plan_id=execution.action_plan_id,
            kind=execution.kind,
            source_location=execution.source_location,
            target_location=execution.target_location,
        )

    def restore(self, request: RestoreRequest) -> ServiceExecutionResult:
        execution = restore_quarantine_coordinated(
            CoordinatedExecution(
                action_plan_id=request.action_plan_id,
                operator=request.operator,
                idempotency_key=request.idempotency_key,
                lease_owner=request.lease_owner,
                lease_ttl_seconds=request.lease_ttl_seconds,
            ),
            self._filesystem,
            self._clock,
            self._uow_factory,
        )
        return ServiceExecutionResult(
            execution_id=execution.id,
            action_plan_id=execution.action_plan_id,
            kind=execution.kind,
            source_location=execution.source_location,
            target_location=execution.target_location,
        )

    def reconcile(
        self,
        request: ReconcileRequest,
    ) -> ServiceReconciliationResult:
        finding = reconcile_action_plan(
            ReconcileActionPlan(request.action_plan_id),
            self._filesystem,
            self._clock,
            self._uow_factory,
        )
        return ServiceReconciliationResult(
            finding_id=finding.id,
            action_plan_id=finding.action_plan_id,
            status=finding.status,
            proposed_action=finding.proposed_action,
            detail=finding.detail,
        )
