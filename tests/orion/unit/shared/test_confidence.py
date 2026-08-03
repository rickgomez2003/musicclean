import pytest

from musicclean.orion.shared import Confidence, DomainValidationError


def test_confidence_accepts_bounds() -> None:
    assert Confidence(0.0).percent == 0.0
    assert Confidence(1.0).percent == 100.0


def test_confidence_from_percent() -> None:
    assert Confidence.from_percent(99.5).value == pytest.approx(0.995)


@pytest.mark.parametrize("value", [-0.01, 1.01])
def test_confidence_rejects_out_of_range(value: float) -> None:
    with pytest.raises(DomainValidationError):
        Confidence(value)
