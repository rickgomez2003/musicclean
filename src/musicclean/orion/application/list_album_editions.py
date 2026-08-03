"""List-album-editions application query."""

from __future__ import annotations

from dataclasses import dataclass

from musicclean.orion.application.errors import NotFoundError
from musicclean.orion.domain import Edition
from musicclean.orion.ports import UnitOfWorkFactory
from musicclean.orion.shared import EntityId


@dataclass(frozen=True, slots=True)
class ListAlbumEditions:
    """Query for all known editions of one Album."""

    album_id: EntityId


def list_album_editions(
    query: ListAlbumEditions,
    uow_factory: UnitOfWorkFactory,
) -> tuple[Edition, ...]:
    """Return known editions for an existing Album."""
    with uow_factory() as uow:
        if uow.albums.get(query.album_id) is None:
            raise NotFoundError(f"album not found: {query.album_id}")
        return uow.editions.list_for_album(query.album_id)
