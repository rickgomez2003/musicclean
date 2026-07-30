from __future__ import annotations

from pathlib import Path

from blake3 import blake3


def hash_file(path: Path, chunk_size: int = 4_194_304) -> str:
    """Return the BLAKE3 digest of a file using bounded-memory streaming."""
    digest = blake3()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()
