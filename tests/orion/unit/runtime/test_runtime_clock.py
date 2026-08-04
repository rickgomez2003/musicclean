from datetime import UTC

from musicclean.orion.runtime.clock import UtcSystemClock


def test_system_clock_returns_utc_aware_timestamp() -> None:
    value = UtcSystemClock().now()

    assert value.tzinfo is UTC
