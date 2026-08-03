from dataclasses import FrozenInstanceError

import pytest

from musicclean.orion.domain import Album


def test_domain_entities_are_immutable() -> None:
    album = Album("Album")

    with pytest.raises(FrozenInstanceError):
        album.title = "Changed"  # type: ignore[misc]
