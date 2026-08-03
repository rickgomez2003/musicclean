"""Artist domain entity."""

from __future__ import annotations

from dataclasses import dataclass, field

from musicclean.orion.domain._validation import optional_text, require_text
from musicclean.orion.shared import EntityId


@dataclass(frozen=True, slots=True)
class Artist:
    """A credited creator or performer independent of filesystem naming."""

    name: str
    id: EntityId = field(default_factory=EntityId.new)
    sort_name: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", require_text(self.name, "artist name"))
        object.__setattr__(self, "sort_name", optional_text(self.sort_name))
