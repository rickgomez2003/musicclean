"""SQLite implementation of the Orion UnitOfWork port."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from types import TracebackType

from musicclean.orion.adapters.sqlite.connection import connect_sqlite
from musicclean.orion.adapters.sqlite.migrations import migrate
from musicclean.orion.adapters.sqlite.repositories import (
    SqliteAlbumRepository,
    SqliteArtistRepository,
    SqliteAudioFileRepository,
    SqliteDiscRepository,
    SqliteEditionRepository,
    SqliteLibraryRepository,
    SqliteRecordingRepository,
    SqliteTrackAppearanceRepository,
)


class SqliteUnitOfWork:
    """Concrete SQLite transaction boundary."""

    def __init__(self, path: str | Path) -> None:
        self._path = path
        self._connection: sqlite3.Connection | None = None

    def __enter__(self) -> SqliteUnitOfWork:
        connection = connect_sqlite(self._path)
        migrate(connection)
        connection.execute("BEGIN")
        self._connection = connection

        self.libraries = SqliteLibraryRepository(connection)
        self.artists = SqliteArtistRepository(connection)
        self.albums = SqliteAlbumRepository(connection)
        self.editions = SqliteEditionRepository(connection)
        self.discs = SqliteDiscRepository(connection)
        self.recordings = SqliteRecordingRepository(connection)
        self.track_appearances = SqliteTrackAppearanceRepository(connection)
        self.audio_files = SqliteAudioFileRepository(connection)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        if self._connection is None:
            return None

        try:
            if exc_type is not None:
                self.rollback()
            else:
                self.rollback()
        finally:
            self._connection.close()
            self._connection = None
        return None

    def commit(self) -> None:
        self._require_connection().commit()
        self._require_connection().execute("BEGIN")

    def rollback(self) -> None:
        connection = self._require_connection()
        connection.rollback()

    def _require_connection(self) -> sqlite3.Connection:
        if self._connection is None:
            raise RuntimeError("SqliteUnitOfWork is not active")
        return self._connection
