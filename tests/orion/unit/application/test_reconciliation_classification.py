from datetime import UTC, datetime

from musicclean.orion.application import classify_reconciliation
from musicclean.orion.domain import ReconciliationAction, ReconciliationStatus
from musicclean.orion.shared import EntityId


def _classify(
    source: bool,
    target: bool,
    quarantine: bool,
    restore: bool,
):
    return classify_reconciliation(
        action_plan_id=EntityId.new(),
        source_exists=source,
        target_exists=target,
        has_quarantine_audit=quarantine,
        has_restore_audit=restore,
        checked_at=datetime.now(UTC),
    )


def test_active_without_audit_is_consistent() -> None:
    finding = _classify(True, False, False, False)
    assert finding.status is ReconciliationStatus.CONSISTENT_ACTIVE
    assert finding.proposed_action is ReconciliationAction.NONE


def test_quarantine_without_audit_is_recoverable() -> None:
    finding = _classify(False, True, False, False)
    assert finding.status is ReconciliationStatus.AUDIT_MISSING_AFTER_QUARANTINE
    assert finding.proposed_action is ReconciliationAction.RECOVER_QUARANTINE_AUDIT


def test_restored_filesystem_with_only_quarantine_audit_is_recoverable() -> None:
    finding = _classify(True, False, True, False)
    assert finding.status is ReconciliationStatus.AUDIT_MISSING_AFTER_RESTORE
    assert finding.proposed_action is ReconciliationAction.RECOVER_RESTORE_AUDIT


def test_both_locations_exist_requires_review() -> None:
    finding = _classify(True, True, False, False)
    assert finding.status is ReconciliationStatus.AMBIGUOUS_BOTH_EXIST
    assert finding.proposed_action is ReconciliationAction.REVIEW


def test_neither_location_exists_requires_review() -> None:
    finding = _classify(False, False, False, False)
    assert finding.status is ReconciliationStatus.MISSING_BOTH
    assert finding.proposed_action is ReconciliationAction.REVIEW
