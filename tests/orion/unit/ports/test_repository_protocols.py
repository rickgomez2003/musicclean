from musicclean.orion.ports import (
    AlbumRepository,
    ArtistRepository,
    AudioFileRepository,
    DiscRepository,
    EditionRepository,
    LibraryRepository,
    RecordingRepository,
    TrackAppearanceRepository,
)


def test_repository_ports_are_protocols() -> None:
    protocols = (
        LibraryRepository,
        ArtistRepository,
        AlbumRepository,
        EditionRepository,
        DiscRepository,
        RecordingRepository,
        TrackAppearanceRepository,
        AudioFileRepository,
    )

    for protocol in protocols:
        assert getattr(protocol, "_is_protocol", False) is True
