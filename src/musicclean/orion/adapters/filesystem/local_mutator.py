"""Local filesystem implementation of FilesystemMutator."""

from __future__ import annotations

import shutil
from pathlib import Path


class LocalFilesystemMutator:
    """Perform no-overwrite local filesystem moves."""

    def exists(self, location: str) -> bool:
        return Path(location).exists()

    def move(self, source: str, target: str) -> None:
        source_path = Path(source)
        target_path = Path(target)

        if not source_path.exists():
            raise FileNotFoundError(source)
        if target_path.exists():
            raise FileExistsError(target)

        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source_path), str(target_path))
