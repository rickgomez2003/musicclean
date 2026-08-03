from pathlib import Path
from types import SimpleNamespace

from musicclean.orion.adapters.metadata import legacy_pipeline
from musicclean.orion.adapters.metadata.legacy_pipeline import LegacyMetadataProvider
from musicclean.orion.ports import MetadataParser


def test_legacy_provider_normalizes_existing_pipeline(monkeypatch) -> None:
    fake = SimpleNamespace(
        title=" Track ",
        artist=" Artist ",
        album=" Album ",
        album_artist=" Album Artist ",
        track_number="1",
        disc_number="1",
        codec="flac",
        bitrate=1234567,
        sample_rate=96000,
        bits_per_sample=24,
        duration=123.45,
        has_artwork=True,
        musicbrainz_track_id="mb-track",
        musicbrainz_album_id="mb-album",
        parser="mutagen",
        parser_warning=None,
    )
    monkeypatch.setattr(legacy_pipeline, "read_audio_metadata", lambda path: fake)

    snapshot = LegacyMetadataProvider().read(Path("/music/track.flac"))

    assert snapshot.title == "Track"
    assert snapshot.artist == "Artist"
    assert snapshot.album == "Album"
    assert snapshot.sample_rate == 96000
    assert snapshot.bits_per_sample == 24
    assert snapshot.parser is MetadataParser.MUTAGEN


def test_legacy_provider_preserves_ffprobe_provenance(monkeypatch) -> None:
    fake = SimpleNamespace(
        title=None,
        artist=None,
        album=None,
        album_artist=None,
        track_number=None,
        disc_number=None,
        codec="wavpack",
        bitrate=None,
        sample_rate=384000,
        bits_per_sample=32,
        duration=600.0,
        has_artwork=False,
        musicbrainz_track_id=None,
        musicbrainz_album_id=None,
        parser="ffprobe",
        parser_warning="Mutagen failed; ffprobe fallback used",
    )
    monkeypatch.setattr(legacy_pipeline, "read_audio_metadata", lambda path: fake)

    snapshot = LegacyMetadataProvider().read(Path("/music/high-rate.wv"))

    assert snapshot.parser is MetadataParser.FFPROBE
    assert snapshot.sample_rate == 384000
    assert snapshot.bits_per_sample == 32
    assert snapshot.parser_warning == "Mutagen failed; ffprobe fallback used"
