# ADR-0010: Use Monotonic Versioned SQLite Migrations

- **Status:** Accepted
- **Date:** 2026-08-03

## Decision

Orion owns a monotonic migration sequence recorded in
`orion_schema_migrations`.

Migrations are applied in version order and are idempotent at the migration-run
level: an applied migration is never applied again.

The initial Orion tables are prefixed `orion_` so the new normalized model can
coexist with the working prototype database during the migration period.

## Rationale

Coexistence lets Orion evolve without forcing an unsafe all-at-once conversion
of the current MusicClean database.

## Future

A later migration/conversion milestone may move Orion into a dedicated database
or retire the legacy schema after parity and rollback procedures are proven.
