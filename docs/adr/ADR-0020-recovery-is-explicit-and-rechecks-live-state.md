# ADR-0020: Recovery Is Explicit and Rechecks Live State

- **Status:** Accepted
- **Date:** 2026-08-03

## Decision

A reconciliation finding may propose recovery, but recovery requires a separate
operator approval.

Immediately before applying recovery Orion re-checks current filesystem state.
If the state has changed since reconciliation, recovery is refused.

Approved recovery does not move files. It writes the missing ExecutionRecord and
marks that record as `origin=recovered`, linked to the ReconciliationFinding that
justified it.

A separate RecoveryRecord links:

- reconciliation finding;
- operator approval;
- recovered execution audit;
- recovery kind;
- operator;
- timestamp.

This preserves the distinction between direct execution history and
operator-approved reconstructed audit history.
