"""Fault-injection fakes used by Orion reliability tests."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class InMemoryFilesystem:
    files: dict[str, bytes] = field(default_factory=dict)
    fail_next_move: bool = False
    moves: list[tuple[str, str]] = field(default_factory=list)

    def exists(self, location: str) -> bool:
        return location in self.files

    def move(self, source: str, target: str) -> None:
        if self.fail_next_move:
            self.fail_next_move = False
            raise OSError("injected move failure")
        if source not in self.files:
            raise FileNotFoundError(source)
        if target in self.files:
            raise FileExistsError(target)
        self.files[target] = self.files.pop(source)
        self.moves.append((source, target))
