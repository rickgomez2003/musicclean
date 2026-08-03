# ADR-0021: Operational Hardening Uses Idempotency and Per-Plan Leases

- **Status:** Accepted
- **Date:** 2026-08-03

## Decision

Operational commands that may be retried use persisted idempotency keys.

ActionPlan execution/recovery coordination uses time-bounded per-plan leases.

A lease has:

- ActionPlan ID
- owner
- acquired timestamp
- expiry timestamp

An active lease blocks a different owner. An expired lease may be replaced.

Startup recovery scans persisted ActionPlans and runs reconciliation without
performing filesystem mutation.

This milestone establishes the coordination primitives; later milestones may
integrate them directly into every executor command.
