"""Library aggregate identity."""

from __future__ import annotations

from dataclasses import dataclass, field

from musicclean.orion.domain._validation import require_text
from musicclean.orion.shared import EntityId


@dataclass(frozen=True, slots=True)
class Library:
    """A managed music collection.

    Storage roots are intentionally not embedded here; they belong to
    application/persistence configuration so a Library can survive path changes.
    """

    name: str
    id: EntityId = field(default_factory=EntityId.new)

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", require_text(self.name, "library name"))
