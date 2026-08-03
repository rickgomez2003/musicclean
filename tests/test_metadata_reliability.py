from pathlib import Path
from typing import Any

import musicclean.metadata as metadata_module
from musicclean.metadata import _first, _has_artwork, _tag, inspect_audio_file


class DangerousSequence:
    def __str__(self) -> str:
        return "safe-value"

    def __getitem__(self, index: int) -> str:
        raise IndexError("list index out of range")


class ApeTextLike:
    value = [" Artist "]


class FakeAudio:
    tags = {"Cover Art (Front)": b"image", "Title": ApeTextLike()}
    info = None


def test_first_does_not_index_arbitrary_sequence_like_values() -> None:
    assert _first(DangerousSequence()) == "safe-value"


def test_first_supports_apev2_value_wrappers() -> None:
    assert _first(ApeTextLike()) == "Artist"


def test_tag_handles_apev2_style_tags() -> None:
    assert _tag({"Album Artist": ApeTextLike()}, "album artist") == "Artist"


def test_artwork_detects_apev2_cover_art() -> None:
    assert _has_artwork(FakeAudio()) is True


def test_inspect_audio_file_reports_parser_details(monkeypatch: Any, tmp_path: Path) -> None:
    sample = tmp_path / "sample.wv"
    sample.write_bytes(b"wvpk")
    monkeypatch.setattr(metadata_module, "MutagenFile", lambda *_args, **_kwargs: FakeAudio())

    result = inspect_audio_file(sample)

    assert result["exists"] is True
    assert result["tag_type"] == "dict"
    assert result["tag_count"] == 2
    assert result["metadata"]["title"] == "Artist"  # type: ignore[index]


def test_inspect_falls_back_to_ffprobe_when_mutagen_wavpack_fails(
    monkeypatch: Any, tmp_path: Path
) -> None:
    sample = tmp_path / "sample.wv"
    sample.write_bytes(b"wvpk")

    def fail_mutagen(*_args: Any, **_kwargs: Any) -> Any:
        raise IndexError("list index out of range")

    monkeypatch.setattr(metadata_module, "MutagenFile", fail_mutagen)
    monkeypatch.setattr(metadata_module, "_read_apev2_tags", lambda _path: None)
    monkeypatch.setattr(
        metadata_module,
        "_ffprobe",
        lambda _path: {
            "streams": [
                {
                    "codec_type": "audio",
                    "codec_name": "wavpack",
                    "codec_long_name": "WavPack",
                    "sample_rate": "384000",
                    "channels": 2,
                    "bits_per_raw_sample": "32",
                    "duration": "1279.302456",
                }
            ],
            "format": {"bit_rate": "14536016"},
        },
    )

    result = inspect_audio_file(sample)

    assert result["parser"] == "ffprobe"
    assert result["warning"] == "Mutagen failed: IndexError: list index out of range"
    assert result["metadata"]["sample_rate"] == 384000  # type: ignore[index]
    assert result["metadata"]["bits_per_sample"] == 32  # type: ignore[index]
