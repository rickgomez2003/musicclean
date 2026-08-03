# ADR-0018: The Initial Executor Is Reversible and No-Overwrite

- **Status:** Accepted
- **Date:** 2026-08-03

## Decision

The first Orion filesystem executor supports only:

- QUARANTINE
- RESTORE

Before a move, it requires:

- a persisted ActionPlan;
- a matching persisted AuthorizationGrant;
- the source to exist;
- the target not to exist;
- no prior execution of the same plan/kind.

The filesystem adapter must never overwrite an existing target.

Completed operations are persisted as immutable ExecutionRecord audit events.

If persistence fails after a successful move, Orion attempts a compensating
move back to the original state before propagating the error.

DELETE remains unsupported.
