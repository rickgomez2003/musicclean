import pytest

from musicclean.orion.domain import Recording
from musicclean.orion.shared import DomainValidationError, Duration


def test_recording_accepts_optional_duration() -> None:
    recording = Recording(" Track ", duration=Duration.from_seconds(123.4))

    assert recording.title == "Track"
    assert recording.duration == Duration(123400)


def test_recording_rejects_blank_title() -> None:
    with pytest.raises(DomainValidationError):
        Recording(" ")
