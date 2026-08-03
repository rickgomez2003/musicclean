from datetime import UTC, datetime

from musicclean.orion.domain import RecoveryApproval, RecoveryKind
from musicclean.orion.shared import EntityId


def test_recovery_approval_records_operator_and_kind() -> None:
    approval = RecoveryApproval(
        finding_id=EntityId.new(),
        kind=RecoveryKind.QUARANTINE_AUDIT,
        approved_by="operator",
        approved_at=datetime.now(UTC),
    )

    assert approval.approved_by == "operator"
    assert approval.kind is RecoveryKind.QUARANTINE_AUDIT
