# Book 14 — Operations

**Status:** Active specification

## Operational hardening

0.6.15 adds coordination primitives for real-world retries, concurrency, and
startup recovery.

### Idempotency

Persisted idempotency keys allow callers to retry a command without creating a
new logical operation each time.

### Per-plan leases

A time-bounded lease coordinates work against one ActionPlan.

- same owner may observe its existing active lease
- different owner is blocked while the lease is active
- an expired lease may be replaced
- only the lease owner may release it

### Startup reconciliation sweep

At startup Orion can enumerate ActionPlans and run reconciliation for each one.

The startup sweep is detection-only. It never performs filesystem mutation or
audit recovery automatically.

## Next hardening step

Executor/recovery use cases can now be wrapped with leases and idempotency so
all externally retried commands share the same operational guarantees.
