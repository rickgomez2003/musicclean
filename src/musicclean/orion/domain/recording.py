"""Recording domain entity."""

from __future__ import annotations

from dataclasses import dataclass, field

from musicclean.orion.domain._validation import require_text
from musicclean.orion.shared import Duration, EntityId


@dataclass(frozen=True, slots=True)
class Recording:
    """A recorded performance independent of edition and file representation."""

    title: str
    id: EntityId = field(default_factory=EntityId.new)
    duration: Duration | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "title", require_text(self.title, "recording title"))
