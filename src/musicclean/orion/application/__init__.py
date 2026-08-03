"""Orion application use cases."""

from musicclean.orion.application.collect_metadata_evidence import (
    CollectMetadataEvidence,
    collect_metadata_evidence,
)
from musicclean.orion.application.create_library import CreateLibrary, create_library
from musicclean.orion.application.errors import ApplicationError, ConflictError, NotFoundError
from musicclean.orion.application.filesystem_sync import (
    FileObservation,
    SyncChange,
    SyncDecision,
    classify_observation,
)
from musicclean.orion.application.infer_knowledge import InferKnowledge, infer_knowledge
from musicclean.orion.application.knowledge_rules import (
    CoreMetadataCompleteRule,
    HighResolutionFormatRule,
    KnowledgeRule,
    latest_evidence_by_kind,
)
from musicclean.orion.application.list_album_editions import (
    ListAlbumEditions,
    list_album_editions,
)
from musicclean.orion.application.read_metadata import ReadMetadata, read_metadata
from musicclean.orion.application.register_audio_file import (
    RegisterAudioFile,
    register_audio_file,
)
from musicclean.orion.application.synchronize_filesystem import (
    SynchronizationSummary,
    SynchronizeFilesystem,
    synchronize_filesystem,
)

__all__ = [
    "ApplicationError",
    "CollectMetadataEvidence",
    "ConflictError",
    "CoreMetadataCompleteRule",
    "CreateLibrary",
    "FileObservation",
    "HighResolutionFormatRule",
    "InferKnowledge",
    "KnowledgeRule",
    "ListAlbumEditions",
    "NotFoundError",
    "ReadMetadata",
    "RegisterAudioFile",
    "SyncChange",
    "SyncDecision",
    "SynchronizationSummary",
    "SynchronizeFilesystem",
    "classify_observation",
    "collect_metadata_evidence",
    "create_library",
    "infer_knowledge",
    "latest_evidence_by_kind",
    "list_album_editions",
    "read_metadata",
    "register_audio_file",
    "synchronize_filesystem",
]
