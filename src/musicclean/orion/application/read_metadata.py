"""Read normalized metadata through a provider port."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from musicclean.orion.ports import MetadataProvider, MetadataSnapshot


@dataclass(frozen=True, slots=True)
class ReadMetadata:
    """Query for reading metadata from one audio file."""

    path: Path


def read_metadata(query: ReadMetadata, provider: MetadataProvider) -> MetadataSnapshot:
    """Read normalized metadata without coupling application code to a parser."""
    return provider.read(query.path)
