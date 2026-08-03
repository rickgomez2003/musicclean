import pytest

from musicclean.orion.domain import Artist
from musicclean.orion.shared import DomainValidationError


def test_artist_normalizes_names() -> None:
    artist = Artist("  The Beatles ", sort_name=" Beatles, The ")
    assert artist.name == "The Beatles"
    assert artist.sort_name == "Beatles, The"


def test_artist_blank_optional_sort_name_becomes_none() -> None:
    assert Artist("Artist", sort_name="   ").sort_name is None


def test_artist_rejects_blank_name() -> None:
    with pytest.raises(DomainValidationError):
        Artist(" ")
