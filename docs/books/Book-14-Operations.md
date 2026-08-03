# Book 14 — Operations

**Status:** Active specification

## Safe action lifecycle

```text
Decision
  -> Review
  -> Authorization
  -> ActionPlan
  -> Preconditions
  -> Filesystem Move
  -> ExecutionRecord
  -> Reconciliation
```

## Crash-recovery gap

Filesystem operations and SQLite commits cannot be one atomic transaction.
A process can therefore stop after a move but before its ExecutionRecord is
committed.

0.6.13 introduces reconciliation to detect this gap.

## Reconciliation

For a persisted ActionPlan Orion compares:

- source existence
- target existence
- quarantine audit presence
- restore audit presence

The result is persisted as a ReconciliationFinding.

## Safety policy

Reconciliation itself never mutates the filesystem and never fabricates an
ExecutionRecord.

Unambiguous missing-audit states can propose recovery. Contradictory or missing
filesystem states require manual review.

This separation keeps detection observable and reviewable before any repair is
attempted.
