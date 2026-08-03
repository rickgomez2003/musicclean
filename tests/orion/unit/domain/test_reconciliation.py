from datetime import UTC, datetime

from musicclean.orion.domain import (
    ReconciliationAction,
    ReconciliationFinding,
    ReconciliationStatus,
)
from musicclean.orion.shared import EntityId


def test_reconciliation_finding_records_observed_state() -> None:
    finding = ReconciliationFinding(
        action_plan_id=EntityId.new(),
        status=ReconciliationStatus.MISSING_BOTH,
        proposed_action=ReconciliationAction.REVIEW,
        source_exists=False,
        target_exists=False,
        has_quarantine_audit=False,
        has_restore_audit=False,
        detail="Manual review required.",
        checked_at=datetime.now(UTC),
    )

    assert finding.proposed_action is ReconciliationAction.REVIEW
