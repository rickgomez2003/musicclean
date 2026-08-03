from pathlib import Path

from musicclean.album_intelligence import build_album_editions


def test_album_scoring_prefers_complete_lossless_edition() -> None:
    rows = [
        {
            "path": "/music/good/01.flac", "directory": "/music/good", "extension": ".flac",
            "artist": "Artist", "album_artist": "Artist", "album": "Album", "title": "Track",
            "track_number": "1", "sample_rate": 96000, "bits_per_sample": 24, "bitrate": 3000000,
            "has_artwork": 1,
            "musicbrainz_track_id": "track-id",
            "musicbrainz_album_id": "album-id",
            "metadata_error": None,
        },
        {
            "path": "/music/weak/01.mp3", "directory": "/music/weak", "extension": ".mp3",
            "artist": None, "album_artist": "Artist", "album": "Album", "title": None,
            "track_number": "1", "sample_rate": 44100, "bits_per_sample": None, "bitrate": 128000,
            "has_artwork": 0, "musicbrainz_track_id": None, "musicbrainz_album_id": None,
            "metadata_error": "bad tags",
        },
    ]
    editions = build_album_editions(rows)
    assert len(editions) == 2
    assert editions[0].directory == Path("/music/good")
    assert editions[0].score > editions[1].score
    assert editions[0].recommendation in {"Keep", "Archive"}
