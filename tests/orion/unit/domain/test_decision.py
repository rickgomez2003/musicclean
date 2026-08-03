from datetime import UTC, datetime

import pytest

from musicclean.orion.domain import Decision, DecisionAction
from musicclean.orion.shared import Confidence, EntityId


def test_decision_requires_knowledge_ids() -> None:
    with pytest.raises(ValueError, match="at least one knowledge"):
        Decision(
            subject_id=EntityId.new(),
            action=DecisionAction.REVIEW,
            confidence=Confidence(1.0),
            rationale="Review this item.",
            knowledge_ids=(),
            rule_id="decision.test",
            rule_version="1",
            decided_at=datetime.now(UTC),
        )
