import pytest

from musicclean.orion.domain import Album
from musicclean.orion.shared import DomainValidationError


def test_album_normalizes_title() -> None:
    assert Album("  Abbey Road  ").title == "Abbey Road"


def test_album_rejects_blank_title() -> None:
    with pytest.raises(DomainValidationError):
        Album("")
