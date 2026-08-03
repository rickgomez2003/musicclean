"""TrackAppearance domain entity."""

from __future__ import annotations

from dataclasses import dataclass, field

from musicclean.orion.domain._validation import optional_text
from musicclean.orion.shared import DomainValidationError, EntityId


@dataclass(frozen=True, slots=True)
class TrackAppearance:
    """Placement of a Recording on a Disc within a particular Edition."""

    disc_id: EntityId
    recording_id: EntityId
    position: int
    id: EntityId = field(default_factory=EntityId.new)
    title_override: str | None = None

    def __post_init__(self) -> None:
        if isinstance(self.position, bool) or self.position < 1:
            raise DomainValidationError("track position must be a positive integer")
        object.__setattr__(self, "title_override", optional_text(self.title_override))
