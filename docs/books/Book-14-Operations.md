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
```

0.6.12 introduces the first real filesystem mutation boundary.

## Supported execution

Only reversible operations are implemented:

- quarantine move
- restore from quarantine

There is no delete executor.

## Preconditions

The executor verifies immediately before mutation:

- ActionPlan exists;
- plan action is QUARANTINE;
- referenced authorization exists;
- authorization belongs to the same Decision;
- source exists;
- target does not exist;
- the plan has not already been executed for that operation kind.

## No-overwrite rule

The filesystem adapter independently refuses to overwrite a target, even if an
application-layer precondition check previously passed.

## Audit

Every successful move creates an immutable ExecutionRecord containing:

- ActionPlan ID
- operation kind
- source and target
- operator
- timestamp

## Compensation

SQLite and filesystem mutation cannot share one atomic transaction. If the file
move succeeds but persistence of its audit record fails, Orion attempts a
compensating move back to the original location.

A later milestone will strengthen crash recovery and reconciliation for failures
that occur between filesystem mutation and audit persistence.
