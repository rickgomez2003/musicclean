"""Register-audio-file application use case."""

from __future__ import annotations

from dataclasses import dataclass

from musicclean.orion.application.errors import NotFoundError
from musicclean.orion.domain import AudioFile
from musicclean.orion.ports import UnitOfWorkFactory
from musicclean.orion.shared import ByteSize, EntityId


@dataclass(frozen=True, slots=True)
class RegisterAudioFile:
    """Command representing one discovered audio-file location."""

    location: str
    size_bytes: int
    recording_id: EntityId | None = None


def register_audio_file(
    command: RegisterAudioFile,
    uow_factory: UnitOfWorkFactory,
) -> AudioFile:
    """Create or refresh an AudioFile while preserving stable identity.

    Re-registering a known location updates mutable observations such as size
    and recording association while keeping the original AudioFile EntityId.
    """
    with uow_factory() as uow:
        if command.recording_id is not None and uow.recordings.get(command.recording_id) is None:
            raise NotFoundError(f"recording not found: {command.recording_id}")

        existing = uow.audio_files.get_by_location(command.location)
        if existing is None:
            audio_file = AudioFile(
                location=command.location,
                size=ByteSize(command.size_bytes),
                recording_id=command.recording_id,
            )
        else:
            audio_file = AudioFile(
                id=existing.id,
                location=command.location,
                size=ByteSize(command.size_bytes),
                recording_id=command.recording_id,
            )

        uow.audio_files.save(audio_file)
        uow.commit()

    return audio_file
