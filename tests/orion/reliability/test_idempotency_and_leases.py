from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from musicclean.orion.adapters.sqlite import SqliteUnitOfWork
from musicclean.orion.application import (
    AcquirePlanLease,
    BeginIdempotentOperation,
    ConflictError,
    acquire_plan_lease,
    begin_idempotent_operation,
    complete_idempotent_operation,
    release_plan_lease,
)
from musicclean.orion.domain import IdempotencyStatus
from musicclean.orion.shared import EntityId, FrozenClock


def test_completed_idempotency_key_is_stable(tmp_path: Path) -> None:
    db_path = tmp_path / "orion.db"
    clock = FrozenClock(datetime(2026, 8, 3, tzinfo=UTC))

    def factory() -> SqliteUnitOfWork:
        return SqliteUnitOfWork(db_path)

    command = BeginIdempotentOperation(
        "stable-key",
        "execute-quarantine",
        EntityId.new(),
    )
    begin_idempotent_operation(command, clock, factory)
    complete_idempotent_operation(command.key, clock, factory)

    retry = begin_idempotent_operation(command, clock, factory)
    assert retry.status is IdempotencyStatus.COMPLETED


def test_active_lease_excludes_other_workers_and_expiry_allows_takeover(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "orion.db"
    plan_id = EntityId.new()
    start = datetime(2026, 8, 3, tzinfo=UTC)

    def factory() -> SqliteUnitOfWork:
        return SqliteUnitOfWork(db_path)

    acquire_plan_lease(
        AcquirePlanLease(plan_id, "worker-a", 30),
        FrozenClock(start),
        factory,
    )

    with pytest.raises(ConflictError, match="another owner"):
        acquire_plan_lease(
            AcquirePlanLease(plan_id, "worker-b", 30),
            FrozenClock(start),
            factory,
        )

    acquire_plan_lease(
        AcquirePlanLease(plan_id, "worker-b", 30),
        FrozenClock(start + timedelta(seconds=31)),
        factory,
    )

    with pytest.raises(ConflictError, match="lease owner"):
        release_plan_lease(plan_id, "worker-a", factory)

    release_plan_lease(plan_id, "worker-b", factory)
