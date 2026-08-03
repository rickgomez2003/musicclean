from pathlib import Path

from musicclean.orion.adapters.sqlite import SqliteUnitOfWork
from musicclean.orion.application import (
    FileObservation,
    SynchronizeFilesystem,
    synchronize_filesystem,
)


class FakeObserver:
    def __init__(self, observations: tuple[FileObservation, ...]) -> None:
        self._observations = observations

    def observe(self, root: str):
        assert root == "/music"
        return self._observations


def _factory(db_path: Path):
    return lambda: SqliteUnitOfWork(db_path)


def test_sync_discovers_then_unchanged(tmp_path: Path) -> None:
    db_path = tmp_path / "orion.db"
    observer = FakeObserver((FileObservation("/music/a.flac", 100),))
    first = synchronize_filesystem(SynchronizeFilesystem("/music"), observer, _factory(db_path))
    second = synchronize_filesystem(SynchronizeFilesystem("/music"), observer, _factory(db_path))
    assert first.discovered == 1
    assert second.unchanged == 1


def test_sync_updates_modified_file_preserving_identity(tmp_path: Path) -> None:
    db_path = tmp_path / "orion.db"
    synchronize_filesystem(
        SynchronizeFilesystem("/music"),
        FakeObserver((FileObservation("/music/a.flac", 100),)),
        _factory(db_path),
    )
    with SqliteUnitOfWork(db_path) as uow:
        original = uow.audio_files.get_by_location("/music/a.flac")
        assert original is not None
        original_id = original.id

    result = synchronize_filesystem(
        SynchronizeFilesystem("/music"),
        FakeObserver((FileObservation("/music/a.flac", 200),)),
        _factory(db_path),
    )
    with SqliteUnitOfWork(db_path) as uow:
        refreshed = uow.audio_files.get_by_location("/music/a.flac")
        assert refreshed is not None
        assert refreshed.id == original_id
        assert refreshed.size.bytes == 200
    assert result.modified == 1
