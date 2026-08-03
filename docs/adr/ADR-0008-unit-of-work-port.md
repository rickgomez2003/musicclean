# ADR-0008: Use an Explicit Unit of Work Port

- **Status:** Accepted
- **Date:** 2026-08-03

## Context

Many MusicClean use cases will modify multiple related records and must either
complete atomically or leave persistence unchanged.

## Decision

Application use cases that require atomic persistence operate through a
`UnitOfWork` port.

The port exposes domain repositories and explicit `commit()` / `rollback()`
semantics. Concrete transaction behavior belongs to adapters.

## Consequences

- application code does not manage SQLite connections directly;
- tests can supply deterministic in-memory implementations;
- transaction boundaries become visible at the use-case level;
- adapter implementations must provide correct rollback behavior.
