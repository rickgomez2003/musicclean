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
    EvidenceRepository,
    LibraryRepository,
    RecordingRepository,
    TrackAppearanceRepository,
)


class UnitOfWork(Protocol):
    libraries: LibraryRepository
    artists: ArtistRepository
    albums: AlbumRepository
    editions: EditionRepository
    discs: DiscRepository
    recordings: RecordingRepository
    track_appearances: TrackAppearanceRepository
    audio_files: AudioFileRepository
    evidence: EvidenceRepository

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
    def __call__(self) -> UnitOfWork: ...
