# Book 09 — Decision Engine

**Status:** Active specification

Decisions are explainable recommendations, not commands.

The safety chain is now:

```text
Evidence
  -> Knowledge
  -> Decision
  -> Review
  -> Authorization
  -> ActionPlan
  -> future Execution
```

A rejected review cannot be authorized. An unreviewed Decision cannot be
authorized. A quarantine ActionPlan cannot be created without explicit
authorization.

Destructive execution remains outside the 0.6.11 scope.
