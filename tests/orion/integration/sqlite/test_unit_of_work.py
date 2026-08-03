from pathlib import Path

from musicclean.orion.adapters.sqlite import SqliteUnitOfWork
from musicclean.orion.domain import Album


def test_uncommitted_changes_are_rolled_back_on_exit(tmp_path: Path) -> None:
    db_path = tmp_path / "orion.db"
    album = Album("Transient")

    with SqliteUnitOfWork(db_path) as uow:
        uow.albums.save(album)

    with SqliteUnitOfWork(db_path) as uow:
        assert uow.albums.get(album.id) is None


def test_committed_changes_survive_exit(tmp_path: Path) -> None:
    db_path = tmp_path / "orion.db"
    album = Album("Persistent")

    with SqliteUnitOfWork(db_path) as uow:
        uow.albums.save(album)
        uow.commit()

    with SqliteUnitOfWork(db_path) as uow:
        assert uow.albums.get(album.id) == album


def test_exception_rolls_back(tmp_path: Path) -> None:
    db_path = tmp_path / "orion.db"
    album = Album("Rolled Back")

    try:
        with SqliteUnitOfWork(db_path) as uow:
            uow.albums.save(album)
            raise RuntimeError("boom")
    except RuntimeError:
        pass

    with SqliteUnitOfWork(db_path) as uow:
        assert uow.albums.get(album.id) is None
