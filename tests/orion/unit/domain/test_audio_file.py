import pytest

from musicclean.orion.domain import AudioFile, Recording
from musicclean.orion.shared import ByteSize, DomainValidationError


def test_audio_file_can_exist_before_recording_match() -> None:
    audio_file = AudioFile(location=r"\\nas\music\unknown.flac", size=ByteSize(1234))

    assert audio_file.recording_id is None


def test_audio_file_can_reference_recording() -> None:
    recording = Recording("Track")
    audio_file = AudioFile(
        location="/music/track.flac",
        size=ByteSize(2048),
        recording_id=recording.id,
    )

    assert audio_file.recording_id == recording.id


def test_audio_file_rejects_blank_location() -> None:
    with pytest.raises(DomainValidationError):
        AudioFile(location=" ", size=ByteSize(0))
