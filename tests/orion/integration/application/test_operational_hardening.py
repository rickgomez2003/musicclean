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


def test_idempotency_returns_existing_record_and_completes_once(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "orion.db"
    clock = FrozenClock(datetime(2026, 8, 3, tzinfo=UTC))

    def factory() -> SqliteUnitOfWork:
        return SqliteUnitOfWork(db_path)

    command = BeginIdempotentOperation(
        key="command-123",
        operation="execute-quarantine",
        subject_id=EntityId.new(),
    )
    first = begin_idempotent_operation(command, clock, factory)
    second = begin_idempotent_operation(command, clock, factory)

    assert first == second
    assert first.status is IdempotencyStatus.STARTED

    complete_idempotent_operation("command-123", clock, factory)
    complete_idempotent_operation("command-123", clock, factory)

    with SqliteUnitOfWork(db_path) as uow:
        completed = uow.idempotency.get("command-123")

    assert completed is not None
    assert completed.status is IdempotencyStatus.COMPLETED


def test_plan_lease_blocks_other_owner_until_expiry(tmp_path: Path) -> None:
    db_path = tmp_path / "orion.db"
    plan_id = EntityId.new()

    def factory() -> SqliteUnitOfWork:
        return SqliteUnitOfWork(db_path)

    first_clock = FrozenClock(datetime(2026, 8, 3, tzinfo=UTC))
    lease = acquire_plan_lease(
        AcquirePlanLease(plan_id, "worker-a", ttl_seconds=60),
        first_clock,
        factory,
    )
    assert lease.owner == "worker-a"

    with pytest.raises(ConflictError, match="another owner"):
        acquire_plan_lease(
            AcquirePlanLease(plan_id, "worker-b", ttl_seconds=60),
            first_clock,
            factory,
        )

    later_clock = FrozenClock(datetime(2026, 8, 3, tzinfo=UTC) + timedelta(seconds=61))
    replacement = acquire_plan_lease(
        AcquirePlanLease(plan_id, "worker-b", ttl_seconds=60),
        later_clock,
        factory,
    )
    assert replacement.owner == "worker-b"

    with pytest.raises(ConflictError, match="lease owner"):
        release_plan_lease(plan_id, "worker-a", factory)

    release_plan_lease(plan_id, "worker-b", factory)
