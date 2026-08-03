"""Filesystem synchronization classification."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from musicclean.orion.domain import AudioFile


class SyncChange(StrEnum):
    DISCOVERED = "discovered"
    UNCHANGED = "unchanged"
    MODIFIED = "modified"
    MOVED = "moved"
    MISSING = "missing"
    RESTORED = "restored"


@dataclass(frozen=True, slots=True)
class FileObservation:
    location: str
    size_bytes: int


@dataclass(frozen=True, slots=True)
class SyncDecision:
    change: SyncChange
    observation: FileObservation
    known_file: AudioFile | None = None


def classify_observation(
    observation: FileObservation,
    known_at_location: AudioFile | None,
) -> SyncDecision:
    if known_at_location is None:
        return SyncDecision(SyncChange.DISCOVERED, observation)
    if known_at_location.size.bytes == observation.size_bytes:
        return SyncDecision(SyncChange.UNCHANGED, observation, known_at_location)
    return SyncDecision(SyncChange.MODIFIED, observation, known_at_location)
