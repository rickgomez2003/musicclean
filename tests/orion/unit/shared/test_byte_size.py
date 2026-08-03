import pytest

from musicclean.orion.shared import ByteSize, DomainValidationError


def test_byte_size_conversions() -> None:
    size = ByteSize(1024**3)

    assert size.kib == pytest.approx(1024**2)
    assert size.mib == pytest.approx(1024)
    assert size.gib == pytest.approx(1.0)


def test_byte_size_rejects_negative_values() -> None:
    with pytest.raises(DomainValidationError):
        ByteSize(-1)
