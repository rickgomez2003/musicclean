# Book 02 — Persistence

**Status:** Active specification

## Persistence principle

Persistence is an adapter. The domain model is authoritative and remains usable
without a database session.

## Current implementation

Orion 0.6.4 introduces a standard-library `sqlite3` adapter.

```text
Application
   |
   v
UnitOfWork + Repository Ports
   |
   v
SQLite Adapter
   |
   v
Versioned Orion Schema
```

## Schema coexistence

Initial normalized tables use the `orion_` prefix. This prevents collision with
the working prototype schema while Orion is developed beside it.

Current tables:

- orion_schema_migrations
- orion_libraries
- orion_artists
- orion_albums
- orion_editions
- orion_discs
- orion_recordings
- orion_track_appearances
- orion_audio_files

## Integrity

SQLite foreign-key enforcement is explicitly enabled for every Orion
connection.

Schema constraints enforce durable persistence invariants such as positive disc
and track positions and non-negative byte/duration values.

## Transactions

`SqliteUnitOfWork` opens a concrete transaction boundary.

- `commit()` persists the current unit and begins a new transaction.
- exiting without commit rolls back pending changes.
- exceptions roll back pending changes.

## Migration policy

Schema changes are monotonic migrations tracked in
`orion_schema_migrations`.

Applied migrations are not silently rewritten. Corrections are expressed as new
migrations.

## Deferred decisions

WAL mode, async database access, connection pooling, and ORM adoption remain
deliberately deferred until workloads demonstrate a need.
