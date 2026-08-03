from datetime import UTC, datetime

import pytest

from musicclean.orion.domain import (
    ExecutionKind,
    ExecutionOrigin,
    ExecutionRecord,
)
from musicclean.orion.shared import EntityId


def test_recovered_execution_requires_finding_id() -> None:
    with pytest.raises(ValueError, match="requires recovery_finding_id"):
        ExecutionRecord(
            action_plan_id=EntityId.new(),
            kind=ExecutionKind.QUARANTINE,
            source_location="/music/a.flac",
            target_location="/quarantine/a.flac",
            executed_by="operator",
            executed_at=datetime.now(UTC),
            origin=ExecutionOrigin.RECOVERED,
        )
