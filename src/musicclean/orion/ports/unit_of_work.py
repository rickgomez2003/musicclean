"""Unit-of-work ports for atomic application use cases."""

from __future__ import annotations

from types import TracebackType
from typing import Protocol, Self

from musicclean.orion.ports.repositories import (
    AlbumRepository,
    ArtistRepository,
    AudioFileRepository,
    DiscRepository,
    EditionRepository,
    LibraryRepository,
    RecordingRepository,
    TrackAppearanceRepository,
)


class UnitOfWork(Protocol):
    """Atomic persistence boundary for one application use case."""

    libraries: LibraryRepository
    artists: ArtistRepository
    albums: AlbumRepository
    editions: EditionRepository
    discs: DiscRepository
    recordings: RecordingRepository
    track_appearances: TrackAppearanceRepository
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


class UnitOfWorkFactory(Protocol):
    """Factory for creating a fresh UnitOfWork per application operation."""

    def __call__(self) -> UnitOfWork: ...
