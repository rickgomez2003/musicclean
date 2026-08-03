"""Unit-of-work port for atomic application use cases."""

from __future__ import annotations

from types import TracebackType
from typing import Protocol, Self

from musicclean.orion.ports.repositories import (
    AlbumRepository,
    ArtistRepository,
    AudioFileRepository,
    EditionRepository,
    LibraryRepository,
    RecordingRepository,
)


class UnitOfWork(Protocol):
    """Atomic persistence boundary for one application use case.

    Concrete adapters may use SQLite transactions, another relational database,
    or an in-memory implementation for tests.
    """

    libraries: LibraryRepository
    artists: ArtistRepository
    albums: AlbumRepository
    editions: EditionRepository
    recordings: RecordingRepository
    audio_files: AudioFileRepository

    def __enter__(self) -> Self: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None: ...

    def commit(self) -> None: ...
    def rollback(self) -> None: ...
