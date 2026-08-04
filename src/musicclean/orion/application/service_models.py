"""Transport-neutral request/response models for the Orion service boundary."""

from __future__ import annotations

from dataclasses import dataclass

from musicclean.orion.domain import (
    ExecutionKind,
    ReconciliationAction,
    ReconciliationStatus,
)
from musicclean.orion.shared import EntityId


@dataclass(frozen=True, slots=True)
class ServiceExecutionResult:
    execution_id: EntityId
    action_plan_id: EntityId
    kind: ExecutionKind
    source_location: str
    target_location: str


@dataclass(frozen=True, slots=True)
class ServiceReconciliationResult:
    finding_id: EntityId
    action_plan_id: EntityId
    status: ReconciliationStatus
    proposed_action: ReconciliationAction
    detail: str


@dataclass(frozen=True, slots=True)
class ServiceHealth:
    service: str
    status: str
    schema_version: int
