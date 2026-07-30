from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class FileRecord:
    path: Path
    root_name: str
    directory: Path
    filename: str
    extension: str
    size: int
    modified_ns: int
    inode: int
    device: int
