from typing import runtime_checkable

from musicclean.orion.ports import (
    AlbumRepository,
    ArtistRepository,
    AudioFileRepository,
    EditionRepository,
    LibraryRepository,
    RecordingRepository,
)


def test_repository_ports_are_protocols() -> None:
    protocols = (
        LibraryRepository,
        ArtistRepository,
        AlbumRepository,
        EditionRepository,
        RecordingRepository,
        AudioFileRepository,
    )

    for protocol in protocols:
        assert getattr(protocol, "_is_protocol", False) is True
        assert runtime_checkable is not None
