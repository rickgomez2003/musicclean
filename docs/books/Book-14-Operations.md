# Book 14 — Operations

**Status:** Active specification

## Reliability harness

0.6.17 intentionally adds no new production behavior.

The milestone adds fault-injection and invariant tests around execution,
reconciliation, idempotency, leases, and audit history.

The acceptance target is stronger than "the command succeeds": safety
invariants must remain true when operations fail, retry, overlap, restart, or
encounter stale state.

## Verified invariants

- failed filesystem moves do not create execution audit records;
- post-move/pre-audit crash state is detected without filesystem mutation;
- completed idempotency keys remain stable under retry;
- active leases exclude other workers;
- expired leases can be taken over;
- a previous lease owner cannot release the replacement lease;
- a successful quarantine/restore lifecycle records exactly one event of each
  kind and returns the file to its source location.
