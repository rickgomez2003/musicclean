from musicclean.orion.application import FileObservation, SyncChange, classify_observation
from musicclean.orion.domain import AudioFile
from musicclean.orion.shared import ByteSize


def test_unknown_is_discovered() -> None:
    assert (
        classify_observation(FileObservation("/music/new.flac", 100), None).change
        is SyncChange.DISCOVERED
    )


def test_same_size_is_unchanged() -> None:
    known = AudioFile(location="/music/a.flac", size=ByteSize(100))
    assert (
        classify_observation(FileObservation("/music/a.flac", 100), known).change
        is SyncChange.UNCHANGED
    )


def test_changed_size_is_modified() -> None:
    known = AudioFile(location="/music/a.flac", size=ByteSize(100))
    assert (
        classify_observation(FileObservation("/music/a.flac", 200), known).change
        is SyncChange.MODIFIED
    )
