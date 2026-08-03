from datetime import UTC, datetime, timedelta

from musicclean.orion.domain import ActionPlanLease, IdempotencyStatus
from musicclean.orion.shared import EntityId


def test_lease_expiry_is_time_bounded() -> None:
    start = datetime(2026, 8, 3, tzinfo=UTC)
    lease = ActionPlanLease(
        action_plan_id=EntityId.new(),
        owner="worker-a",
        acquired_at=start,
        expires_at=start + timedelta(seconds=60),
    )
    assert lease.is_active_at(start + timedelta(seconds=59))
    assert not lease.is_active_at(start + timedelta(seconds=60))


def test_idempotency_status_values_are_stable() -> None:
    assert IdempotencyStatus.STARTED.value == "started"
    assert IdempotencyStatus.COMPLETED.value == "completed"
