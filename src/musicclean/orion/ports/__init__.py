"""Abstract ports implemented by Orion adapters."""

from musicclean.orion.ports.filesystem import FilesystemObserver
from musicclean.orion.ports.metadata import (
    MetadataParser,
    MetadataProvider,
    MetadataSnapshot,
)
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
from musicclean.orion.ports.unit_of_work import UnitOfWork, UnitOfWorkFactory

__all__ = [
    "AlbumRepository",
    "ArtistRepository",
    "AudioFileRepository",
    "DiscRepository",
    "EditionRepository",
    "FilesystemObserver",
    "LibraryRepository",
    "MetadataParser",
    "MetadataProvider",
    "MetadataSnapshot",
    "RecordingRepository",
    "TrackAppearanceRepository",
    "UnitOfWork",
    "UnitOfWorkFactory",
]
