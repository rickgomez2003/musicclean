import pytest

from musicclean.orion.shared import BitDepth, DomainValidationError, SampleRate


@pytest.mark.parametrize("hz", [44100, 48000, 96000, 192000, 384000])
def test_sample_rate_accepts_realistic_values(hz: int) -> None:
    assert SampleRate(hz).hz == hz


@pytest.mark.parametrize("bits", [16, 20, 24, 32])
def test_bit_depth_accepts_realistic_values(bits: int) -> None:
    assert BitDepth(bits).bits == bits


@pytest.mark.parametrize("hz", [0, -1])
def test_sample_rate_rejects_non_positive_values(hz: int) -> None:
    with pytest.raises(DomainValidationError):
        SampleRate(hz)


@pytest.mark.parametrize("bits", [0, -1])
def test_bit_depth_rejects_non_positive_values(bits: int) -> None:
    with pytest.raises(DomainValidationError):
        BitDepth(bits)
