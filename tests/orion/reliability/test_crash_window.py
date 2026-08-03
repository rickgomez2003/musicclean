from datetime import UTC, datetime
from pathlib import Path

from musicclean.orion.adapters.sqlite import SqliteUnitOfWork
from musicclean.orion.application import ReconcileActionPlan, reconcile_action_plan
from musicclean.orion.domain import ReconciliationAction, ReconciliationStatus
from musicclean.orion.shared import FrozenClock

from .fakes import InMemoryFilesystem
from .helpers import seed_action_plan


def test_post_move_pre_audit_crash_is_detected_without_mutation(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "orion.db"
    source = "/music/a.flac"
    target = "/quarantine/a.flac"
    plan = seed_action_plan(db_path, source, target)
    filesystem = InMemoryFilesystem(files={target: b"audio"})

    def factory() -> SqliteUnitOfWork:
        return SqliteUnitOfWork(db_path)

    finding = reconcile_action_plan(
        ReconcileActionPlan(plan.id),
        filesystem,
        FrozenClock(datetime(2026, 8, 3, 2, 0, tzinfo=UTC)),
        factory,
    )

    assert finding.status is ReconciliationStatus.AUDIT_MISSING_AFTER_QUARANTINE
    assert finding.proposed_action is ReconciliationAction.RECOVER_QUARANTINE_AUDIT
    assert filesystem.files == {target: b"audio"}
    assert filesystem.moves == []
