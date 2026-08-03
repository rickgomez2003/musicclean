"""AudioFile domain entity."""

from __future__ import annotations

from dataclasses import dataclass, field

from musicclean.orion.domain._validation import require_text
from musicclean.orion.shared import ByteSize, EntityId


@dataclass(frozen=True, slots=True)
class AudioFile:
    """A concrete digital representation of audio at a mutable location.

    `recording_id` is optional because files may exist before Orion has enough
    evidence to associate them with a Recording.
    """

    location: str
    size: ByteSize
    id: EntityId = field(default_factory=EntityId.new)
    recording_id: EntityId | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "location", require_text(self.location, "audio file location"))
