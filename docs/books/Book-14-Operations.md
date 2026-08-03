# Book 14 — Operations

**Status:** Active specification

## Coordinated execution

0.6.16 connects operational-hardening primitives to real executor paths.

A coordinated command now follows:

```text
Idempotency Key
    ↓
Atomic ActionPlan Lease
    ↓
Executor / Recovery Use Case
    ↓
Persisted Result
    ↓
Idempotency Completion
    ↓
Lease Release
```

## Atomic lease acquisition

SQLite uses a single conditional UPSERT.

A lease can be written when:

- no lease exists;
- the existing lease is expired; or
- the existing lease belongs to the same owner.

An active lease owned by another worker is not modified.

## Idempotent result handling

If an idempotency key is already COMPLETED, the coordinated path retrieves and
returns the existing ExecutionRecord or RecoveryRecord.

It does not repeat the filesystem mutation.

An idempotency key is permanently associated with its operation and subject.
A collision with another logical command is rejected.

## Failure cleanup

Lease release occurs in a `finally` block. This handles ordinary application
exceptions.

A hard process crash may still leave the lease persisted until expiration,
which is intentional. Startup reconciliation and lease expiry provide the
recovery path.
