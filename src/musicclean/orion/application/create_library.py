"""Create-library application use case."""

from __future__ import annotations

from dataclasses import dataclass

from musicclean.orion.application.errors import ConflictError
from musicclean.orion.domain import Library
from musicclean.orion.ports import UnitOfWorkFactory


@dataclass(frozen=True, slots=True)
class CreateLibrary:
    """Command for creating a managed Library."""

    name: str


def create_library(command: CreateLibrary, uow_factory: UnitOfWorkFactory) -> Library:
    """Create and persist a Library with a case-insensitively unique name."""
    library = Library(command.name)

    with uow_factory() as uow:
        if any(
            existing.name.casefold() == library.name.casefold()
            for existing in uow.libraries.list_all()
        ):
            raise ConflictError(f"library already exists: {library.name}")

        uow.libraries.save(library)
        uow.commit()

    return library
