"""Synchronize observed files with known AudioFile state."""

from __future__ import annotations

from dataclasses import dataclass

from musicclean.orion.application.filesystem_sync import SyncChange, classify_observation
from musicclean.orion.domain import AudioFile
from musicclean.orion.ports import FilesystemObserver, UnitOfWorkFactory
from musicclean.orion.shared import ByteSize


@dataclass(frozen=True, slots=True)
class SynchronizeFilesystem:
    root: str


@dataclass(frozen=True, slots=True)
class SynchronizationSummary:
    discovered: int = 0
    unchanged: int = 0
    modified: int = 0


def synchronize_filesystem(
    command: SynchronizeFilesystem,
    observer: FilesystemObserver,
    uow_factory: UnitOfWorkFactory,
) -> SynchronizationSummary:
    discovered = unchanged = modified = 0
    with uow_factory() as uow:
        for observation in observer.observe(command.root):
            known = uow.audio_files.get_by_location(observation.location)
            decision = classify_observation(observation, known)

            if decision.change is SyncChange.DISCOVERED:
                uow.audio_files.save(
                    AudioFile(
                        location=observation.location,
                        size=ByteSize(observation.size_bytes),
                    )
                )
                discovered += 1
            elif decision.change is SyncChange.MODIFIED:
                assert decision.known_file is not None
                uow.audio_files.save(
                    AudioFile(
                        id=decision.known_file.id,
                        location=observation.location,
                        size=ByteSize(observation.size_bytes),
                        recording_id=decision.known_file.recording_id,
                    )
                )
                modified += 1
            else:
                unchanged += 1
        uow.commit()

    return SynchronizationSummary(discovered, unchanged, modified)
