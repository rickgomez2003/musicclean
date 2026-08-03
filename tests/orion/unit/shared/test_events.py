from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta, timezone

import pytest

from musicclean.orion.shared import DomainEvent


def test_domain_event_has_id_and_utc_timestamp() -> None:
    event = DomainEvent()

    assert event.event_id is not None
    assert event.occurred_at.utcoffset() == timedelta(0)


def test_domain_event_normalizes_timestamp_to_utc() -> None:
    source = datetime(2026, 8, 3, 10, 0, tzinfo=timezone(timedelta(hours=-4)))

    event = DomainEvent(occurred_at=source)

    assert event.occurred_at == datetime(2026, 8, 3, 14, 0, tzinfo=UTC)


def test_domain_event_rejects_naive_timestamp() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        DomainEvent(occurred_at=datetime(2026, 8, 3, 10, 0))


def test_domain_event_is_immutable() -> None:
    event = DomainEvent()

    with pytest.raises(FrozenInstanceError):
        event.occurred_at = datetime.now(UTC)  # type: ignore[misc]
