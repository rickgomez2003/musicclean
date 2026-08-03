import pytest

from musicclean.orion.domain import Library
from musicclean.orion.shared import DomainValidationError


def test_library_normalizes_name() -> None:
    library = Library("  Main Music  ")
    assert library.name == "Main Music"


def test_library_rejects_blank_name() -> None:
    with pytest.raises(DomainValidationError):
        Library("   ")
