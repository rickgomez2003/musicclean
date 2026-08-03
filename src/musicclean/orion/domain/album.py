"""Album domain entity."""

from __future__ import annotations

from dataclasses import dataclass, field

from musicclean.orion.domain._validation import require_text
from musicclean.orion.shared import EntityId


@dataclass(frozen=True, slots=True)
class Album:
    """An abstract release concept independent of a particular edition."""

    title: str
    id: EntityId = field(default_factory=EntityId.new)

    def __post_init__(self) -> None:
        object.__setattr__(self, "title", require_text(self.title, "album title"))
