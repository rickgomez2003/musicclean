# ADR-0017: Require Review and Explicit Authorization Before Execution

- **Status:** Accepted
- **Date:** 2026-08-03

## Decision

Recommendations cannot directly mutate a music library.

The safety chain is:

```text
Decision
  -> Review
  -> Authorization
  -> ActionPlan
  -> future Executor
```

0.6.11 stops at ActionPlan.

Quarantine planning also produces an UndoDescriptor describing how a future
quarantine operation would be reversed.

No filesystem move, rename, tag write, overwrite, or delete operation is
implemented in this milestone.
