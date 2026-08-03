# Book 14 — Operations

**Status:** Active specification

## Safe action lifecycle

```text
Decision
  -> Review
  -> Authorization
  -> ActionPlan
  -> Filesystem execution
  -> ExecutionRecord
  -> Reconciliation
  -> Recovery Approval
  -> Recovery Record
```

## Recovery policy

0.6.14 implements the repair side of reconciliation.

The governing rule is:

> detect automatically, repair deliberately.

A finding that proposes audit recovery cannot repair itself. An operator must
approve that specific finding.

Immediately before recovery Orion checks the filesystem again. If the live state
no longer matches the approved recovery condition, the operation is refused.

## Recovered audit history

Recovery never moves the file.

It creates the missing ExecutionRecord with:

- `origin = recovered`
- `recovery_finding_id = <finding>`

A RecoveryRecord separately preserves the approval and repair history.

This prevents reconstructed history from being indistinguishable from an audit
record written during a normal direct execution.
