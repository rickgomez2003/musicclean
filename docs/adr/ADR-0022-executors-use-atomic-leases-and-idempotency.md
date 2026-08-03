# ADR-0022: Executors Use Atomic Leases and Idempotency

- **Status:** Accepted
- **Date:** 2026-08-03

## Decision

Coordinated execution paths bind each externally retried command to:

1. a persisted idempotency key; and
2. a time-bounded ActionPlan lease.

SQLite lease acquisition is a single conditional UPSERT. An active lease held
by another owner cannot be overwritten. An expired lease may be replaced.

A completed idempotency record returns the existing domain result rather than
executing the filesystem operation again.

Lease release occurs in `finally` blocks so application failures do not
intentionally retain the lease.

Idempotency keys are also bound to operation + subject. Reusing a key for a
different logical command is rejected.
