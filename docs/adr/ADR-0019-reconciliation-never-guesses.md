# ADR-0019: Reconciliation Detects Mismatches but Never Guesses

- **Status:** Accepted
- **Date:** 2026-08-03

## Decision

After a crash or external filesystem change, Orion compares persisted execution
audit with current source/target existence and records a ReconciliationFinding.

Unambiguous missing-audit states may propose audit recovery, but 0.6.13 does not
write synthetic ExecutionRecords and does not move files.

Ambiguous states always require review.

Examples:

- both source and target exist -> REVIEW
- neither exists -> REVIEW
- target only, no quarantine audit -> RECOVER_QUARANTINE_AUDIT proposal
- source only, quarantine audit but no restore audit -> RECOVER_RESTORE_AUDIT
  proposal

This keeps detection separate from repair and avoids fabricating history.
