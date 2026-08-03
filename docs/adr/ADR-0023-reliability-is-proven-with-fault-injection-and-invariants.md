# ADR-0023: Reliability Is Proven with Fault Injection and Invariants

- **Status:** Accepted
- **Date:** 2026-08-03

## Decision

Orion maintains a dedicated reliability harness before adding more production
behavior after executor coordination.

The harness verifies architectural invariants across:

- filesystem failures;
- crash-window reconciliation;
- idempotent retries;
- lease exclusion and expiry takeover;
- execution-history cardinality and ordering.

SQLite remains real while deterministic test doubles are used for filesystem
fault injection.
