import pytest

from musicclean.orion.shared import DomainValidationError, Duration


def test_duration_from_seconds() -> None:
    duration = Duration.from_seconds(1.234)

    assert duration.milliseconds == 1234
    assert duration.seconds == pytest.approx(1.234)


def test_duration_allows_zero() -> None:
    assert Duration(0).seconds == 0.0


def test_duration_rejects_negative_values() -> None:
    with pytest.raises(DomainValidationError):
        Duration(-1)
