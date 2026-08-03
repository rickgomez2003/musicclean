"""Filesystem observation port."""

from collections.abc import Iterable
from typing import Protocol

from musicclean.orion.application.filesystem_sync import FileObservation


class FilesystemObserver(Protocol):
    def observe(self, root: str) -> Iterable[FileObservation]: ...
