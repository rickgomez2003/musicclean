from datetime import UTC, datetime

import pytest

from musicclean.orion.domain import ActionPlan, PlannedAction
from musicclean.orion.shared import EntityId


def test_action_plan_requires_distinct_locations() -> None:
    with pytest.raises(ValueError, match="must differ"):
        ActionPlan(
            decision_id=EntityId.new(),
            authorization_id=EntityId.new(),
            action=PlannedAction.QUARANTINE,
            source_location="/music/a.flac",
            target_location="/music/a.flac",
            created_at=datetime.now(UTC),
        )
