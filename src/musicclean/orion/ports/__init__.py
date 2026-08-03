"""Abstract ports implemented by Orion adapters."""

from musicclean.orion.ports.filesystem import FilesystemObserver
from musicclean.orion.ports.metadata import MetadataParser, MetadataProvider, MetadataSnapshot
from musicclean.orion.ports.repositories import (
    ActionPlanRepository,
    AlbumRepository,
    ArtistRepository,
    AudioFileRepository,
    AuthorizationRepository,
    DecisionRepository,
    DiscRepository,
    EditionRepository,
    EvidenceRepository,
    KnowledgeRepository,
    LibraryRepository,
    RecordingRepository,
    ReviewRepository,
    TrackAppearanceRepository,
)
from musicclean.orion.ports.unit_of_work import UnitOfWork, UnitOfWorkFactory

__all__ = [
    "ActionPlanRepository",
    "AlbumRepository",
    "ArtistRepository",
    "AudioFileRepository",
    "AuthorizationRepository",
    "DecisionRepository",
    "DiscRepository",
    "EditionRepository",
    "EvidenceRepository",
    "FilesystemObserver",
    "KnowledgeRepository",
    "LibraryRepository",
    "MetadataParser",
    "MetadataProvider",
    "MetadataSnapshot",
    "RecordingRepository",
    "ReviewRepository",
    "TrackAppearanceRepository",
    "UnitOfWork",
    "UnitOfWorkFactory",
]
