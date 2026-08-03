# Book 02 — Persistence

**Status:** Active specification

## Persistence principle

The database is an adapter-backed system of record, not the owner of the domain
model. Domain entities must remain usable without a database session.

## Port boundary

Application code depends on repository ports and a Unit of Work.

```text
Application Use Case
        |
        v
    UnitOfWork
        |
        +-- AlbumRepository
        +-- EditionRepository
        +-- RecordingRepository
        +-- AudioFileRepository
        |
        v
Concrete Adapter (SQLite later)
```

## Repository rules

Repositories:

- accept/return Orion domain entities or domain identifiers;
- expose domain-oriented queries;
- do not expose SQL, cursors, ORM entities, sessions, or query builders;
- do not become a universal generic CRUD interface.

## Transaction rules

The Unit of Work defines an atomic application boundary. Concrete adapters must
commit explicitly and roll back on failure.

## Deferred decisions

Orion 0.6.3 intentionally does not choose:

- SQLAlchemy versus direct SQLite;
- Alembic versus a custom migration runner;
- connection pooling;
- async database access;
- final schema shape.

Those decisions follow from persistence requirements rather than preceding them.
