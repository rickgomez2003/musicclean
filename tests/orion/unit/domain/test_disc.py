import pytest

from musicclean.orion.domain import Album, Disc, Edition
from musicclean.orion.shared import DomainValidationError


def test_disc_references_edition() -> None:
    edition = Edition(album_id=Album("Album").id)
    disc = Disc(edition_id=edition.id, position=2, title=" Bonus Disc ")

    assert disc.edition_id == edition.id
    assert disc.position == 2
    assert disc.title == "Bonus Disc"


@pytest.mark.parametrize("position", [0, -1])
def test_disc_rejects_invalid_position(position: int) -> None:
    edition = Edition(album_id=Album("Album").id)
    with pytest.raises(DomainValidationError):
        Disc(edition_id=edition.id, position=position)
