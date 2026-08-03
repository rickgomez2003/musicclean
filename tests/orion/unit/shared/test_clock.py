from datetime import UTC, datetime, timedelta, timezone

import pytest

from musicclean.orion.shared import FrozenClock, SystemClock


def test_system_clock_returns_aware_utc_datetime() -> None:
    instant = SystemClock().now()

    assert instant.tzinfo is not None
    assert instant.utcoffset() == timedelta(0)


def test_frozen_clock_normalizes_to_utc() -> None:
    source = datetime(2026, 8, 3, 10, 0, tzinfo=timezone(timedelta(hours=-4)))

    instant = FrozenClock(source).now()

    assert instant == datetime(2026, 8, 3, 14, 0, tzinfo=UTC)


def test_frozen_clock_rejects_naive_datetime() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        FrozenClock(datetime(2026, 8, 3, 10, 0))
