from pathlib import Path

from musicclean.orion.application import ReadMetadata, read_metadata
from musicclean.orion.ports import MetadataParser, MetadataSnapshot


class FakeMetadataProvider:
    def read(self, path: Path) -> MetadataSnapshot:
        assert path == Path("/music/track.flac")
        return MetadataSnapshot(
            title="Track",
            artist="Artist",
            parser=MetadataParser.MUTAGEN,
        )


def test_read_metadata_delegates_to_provider() -> None:
    result = read_metadata(ReadMetadata(Path("/music/track.flac")), FakeMetadataProvider())

    assert result.title == "Track"
    assert result.artist == "Artist"
    assert result.parser is MetadataParser.MUTAGEN
