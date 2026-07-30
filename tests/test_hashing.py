from pathlib import Path

from blake3 import blake3

from musicclean.hashing import hash_file


def test_hash_file(tmp_path: Path) -> None:
    path = tmp_path / "sample.bin"
    content = b"MusicClean" * 1000
    path.write_bytes(content)

    assert hash_file(path, chunk_size=37) == blake3(content).hexdigest()
