"""Edition domain entity."""

from __future__ import annotations

from dataclasses import dataclass, field

from musicclean.orion.domain._validation import optional_text
from musicclean.orion.shared import EntityId


@dataclass(frozen=True, slots=True)
class Edition:
    """A specific published version of an Album.

    Format/source labels remain open text at this layer because real collections
    contain many legitimate and ambiguous release descriptions.
    """

    album_id: EntityId
    id: EntityId = field(default_factory=EntityId.new)
    release_label: str | None = None
    media_format: str | None = None
    catalog_number: str | None = None
    barcode: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "release_label", optional_text(self.release_label))
        object.__setattr__(self, "media_format", optional_text(self.media_format))
        object.__setattr__(self, "catalog_number", optional_text(self.catalog_number))
        object.__setattr__(self, "barcode", optional_text(self.barcode))
