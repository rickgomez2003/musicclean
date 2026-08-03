from datetime import UTC, datetime
from pathlib import Path

from musicclean.orion.adapters.sqlite import SqliteUnitOfWork
from musicclean.orion.application import (
    ExecuteQuarantine,
    RestoreQuarantine,
    execute_quarantine,
    restore_quarantine,
)
from musicclean.orion.domain import ExecutionKind
from musicclean.orion.shared import FrozenClock

from .fakes import InMemoryFilesystem
from .helpers import seed_action_plan


def test_successful_lifecycle_has_one_quarantine_and_one_restore(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "orion.db"
    source = "/music/a.flac"
    target = "/quarantine/a.flac"
    plan = seed_action_plan(db_path, source, target)
    filesystem = InMemoryFilesystem(files={source: b"audio"})

    def factory() -> SqliteUnitOfWork:
        return SqliteUnitOfWork(db_path)

    execute_quarantine(
        ExecuteQuarantine(plan.id, "operator"),
        filesystem,
        FrozenClock(datetime(2026, 8, 3, 1, 0, tzinfo=UTC)),
        factory,
    )
    restore_quarantine(
        RestoreQuarantine(plan.id, "operator"),
        filesystem,
        FrozenClock(datetime(2026, 8, 3, 1, 1, tzinfo=UTC)),
        factory,
    )

    with SqliteUnitOfWork(db_path) as uow:
        history = uow.executions.list_for_plan(plan.id)

    assert [event.kind for event in history] == [
        ExecutionKind.QUARANTINE,
        ExecutionKind.RESTORE,
    ]
    assert filesystem.files == {source: b"audio"}
