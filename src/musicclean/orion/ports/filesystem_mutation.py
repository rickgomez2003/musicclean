"""Filesystem mutation port for reversible Orion actions."""

from __future__ import annotations

from typing import Protocol


class FilesystemMutator(Protocol):
    """Minimal filesystem contract used by the safe executor."""

    def exists(self, location: str) -> bool: ...

    def move(self, source: str, target: str) -> None:
        """Move source to target without overwriting an existing target."""
        ...
