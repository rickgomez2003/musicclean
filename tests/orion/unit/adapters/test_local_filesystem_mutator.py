from pathlib import Path

import pytest

from musicclean.orion.adapters.filesystem import LocalFilesystemMutator


def test_local_mutator_moves_without_overwrite(tmp_path: Path) -> None:
    source = tmp_path / "music" / "a.flac"
    target = tmp_path / "quarantine" / "a.flac"
    source.parent.mkdir()
    source.write_bytes(b"audio")

    mutator = LocalFilesystemMutator()
    mutator.move(str(source), str(target))

    assert not source.exists()
    assert target.read_bytes() == b"audio"


def test_local_mutator_refuses_existing_target(tmp_path: Path) -> None:
    source = tmp_path / "a.flac"
    target = tmp_path / "existing.flac"
    source.write_bytes(b"source")
    target.write_bytes(b"target")

    with pytest.raises(FileExistsError):
        LocalFilesystemMutator().move(str(source), str(target))

    assert source.read_bytes() == b"source"
    assert target.read_bytes() == b"target"
