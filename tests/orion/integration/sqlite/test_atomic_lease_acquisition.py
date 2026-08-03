from datetime import UTC, datetime, timedelta
from pathlib import Path

from musicclean.orion.adapters.sqlite import SqliteUnitOfWork
from musicclean.orion.domain import ActionPlanLease
from musicclean.orion.shared import EntityId


def test_atomic_lease_rejects_second_owner_while_active(tmp_path: Path) -> None:
    db_path = tmp_path / "orion.db"
    plan_id = EntityId.new()
    now = datetime(2026, 8, 3, tzinfo=UTC)

    first = ActionPlanLease(
        action_plan_id=plan_id,
        owner="worker-a",
        acquired_at=now,
        expires_at=now + timedelta(seconds=60),
    )
    second = ActionPlanLease(
        action_plan_id=plan_id,
        owner="worker-b",
        acquired_at=now,
        expires_at=now + timedelta(seconds=60),
    )

    with SqliteUnitOfWork(db_path) as uow:
        assert uow.leases.try_acquire(first, now) == first
        uow.commit()

    with SqliteUnitOfWork(db_path) as uow:
        assert uow.leases.try_acquire(second, now) is None


def test_atomic_lease_allows_takeover_after_expiry(tmp_path: Path) -> None:
    db_path = tmp_path / "orion.db"
    plan_id = EntityId.new()
    now = datetime(2026, 8, 3, tzinfo=UTC)

    first = ActionPlanLease(
        action_plan_id=plan_id,
        owner="worker-a",
        acquired_at=now,
        expires_at=now + timedelta(seconds=60),
    )
    later = now + timedelta(seconds=61)
    second = ActionPlanLease(
        action_plan_id=plan_id,
        owner="worker-b",
        acquired_at=later,
        expires_at=later + timedelta(seconds=60),
    )

    with SqliteUnitOfWork(db_path) as uow:
        assert uow.leases.try_acquire(first, now) == first
        uow.commit()

    with SqliteUnitOfWork(db_path) as uow:
        assert uow.leases.try_acquire(second, later) == second
        uow.commit()
