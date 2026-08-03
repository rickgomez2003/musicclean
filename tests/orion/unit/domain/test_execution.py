from datetime import UTC, datetime

import pytest

from musicclean.orion.domain import ExecutionKind, ExecutionRecord
from musicclean.orion.shared import EntityId


def test_execution_requires_distinct_locations() -> None:
    with pytest.raises(ValueError, match="must differ"):
        ExecutionRecord(
            action_plan_id=EntityId.new(),
            kind=ExecutionKind.QUARANTINE,
            source_location="/music/a.flac",
            target_location="/music/a.flac",
            executed_by="operator",
            executed_at=datetime.now(UTC),
        )
