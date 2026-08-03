from datetime import UTC, datetime

import pytest

from musicclean.orion.domain import KnowledgeFact, KnowledgeKind
from musicclean.orion.shared import Confidence, EntityId


def test_knowledge_fact_requires_evidence_ids() -> None:
    with pytest.raises(ValueError, match="at least one evidence"):
        KnowledgeFact(
            subject_id=EntityId.new(),
            kind=KnowledgeKind.CORE_METADATA_COMPLETE,
            value=True,
            confidence=Confidence(1.0),
            evidence_ids=(),
            rule_id="rule",
            rule_version="1",
            inferred_at=datetime.now(UTC),
        )
