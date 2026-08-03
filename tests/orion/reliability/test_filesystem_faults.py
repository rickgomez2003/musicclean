from datetime import UTC, datetime
from pathlib import Path

import pytest

from musicclean.orion.adapters.sqlite import SqliteUnitOfWork
from musicclean.orion.application import ExecuteQuarantine, execute_quarantine
from musicclean.orion.shared import FrozenClock

from .fakes import InMemoryFilesystem
from .helpers import seed_action_plan


def test_move_failure_does_not_create_execution_audit(tmp_path: Path) -> None:
    db_path = tmp_path / "orion.db"
    source = "/music/a.flac"
    target = "/quarantine/a.flac"
    plan = seed_action_plan(db_path, source, target)
    filesystem = InMemoryFilesystem(
        files={source: b"audio"},
        fail_next_move=True,
    )

    def factory() -> SqliteUnitOfWork:
        return SqliteUnitOfWork(db_path)

    with pytest.raises(OSError, match="injected move failure"):
        execute_quarantine(
            ExecuteQuarantine(plan.id, "operator"),
            filesystem,
            FrozenClock(datetime(2026, 8, 3, 1, 0, tzinfo=UTC)),
            factory,
        )

    assert filesystem.files == {source: b"audio"}
    with SqliteUnitOfWork(db_path) as uow:
        assert uow.executions.list_for_plan(plan.id) == ()
