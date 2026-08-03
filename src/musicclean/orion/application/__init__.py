"""Orion application use cases."""

from musicclean.orion.application.create_library import CreateLibrary, create_library
from musicclean.orion.application.errors import ApplicationError, ConflictError, NotFoundError
from musicclean.orion.application.filesystem_sync import (
    FileObservation,
    SyncChange,
    SyncDecision,
    classify_observation,
)
from musicclean.orion.application.list_album_editions import ListAlbumEditions, list_album_editions
from musicclean.orion.application.register_audio_file import RegisterAudioFile, register_audio_file
from musicclean.orion.application.synchronize_filesystem import (
    SynchronizationSummary,
    SynchronizeFilesystem,
    synchronize_filesystem,
)

__all__ = [
    "ApplicationError",
    "ConflictError",
    "CreateLibrary",
    "FileObservation",
    "ListAlbumEditions",
    "NotFoundError",
    "RegisterAudioFile",
    "SyncChange",
    "SyncDecision",
    "SynchronizationSummary",
    "SynchronizeFilesystem",
    "classify_observation",
    "create_library",
    "list_album_editions",
    "register_audio_file",
    "synchronize_filesystem",
]
