"""Abstract ports implemented by Orion adapters."""

from musicclean.orion.ports.filesystem import FilesystemObserver
from musicclean.orion.ports.filesystem_mutation import FilesystemMutator
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
    ExecutionRepository,
    KnowledgeRepository,
    LibraryRepository,
    ReconciliationRepository,
    RecordingRepository,
    RecoveryApprovalRepository,
    RecoveryRepository,
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
    "ExecutionRepository",
    "FilesystemMutator",
    "FilesystemObserver",
    "KnowledgeRepository",
    "LibraryRepository",
    "MetadataParser",
    "MetadataProvider",
    "MetadataSnapshot",
    "ReconciliationRepository",
    "RecordingRepository",
    "RecoveryApprovalRepository",
    "RecoveryRepository",
    "ReviewRepository",
    "TrackAppearanceRepository",
    "UnitOfWork",
    "UnitOfWorkFactory",
]
