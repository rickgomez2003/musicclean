# ADR-0007: Use Domain-Specific Repository Ports

- **Status:** Accepted
- **Date:** 2026-08-03

## Context

A generic `Repository[T]` with universal CRUD methods is attractive but often
pushes persistence-shaped operations into the application layer and obscures
real domain queries.

## Decision

Orion defines repository ports around domain concepts and use cases rather than
a generic repository abstraction.

Initial repositories:

- LibraryRepository
- ArtistRepository
- AlbumRepository
- EditionRepository
- RecordingRepository
- AudioFileRepository

Repository ports use domain entities and `EntityId` values only. They do not
expose SQL rows, ORM sessions, query builders, cursors, or adapter-specific
types.

## Consequences

### Positive
- clearer application intent;
- stronger domain vocabulary;
- adapters remain replaceable;
- no accidental ORM leakage.

### Tradeoffs
- some method signatures may repeat across repositories;
- repository interfaces may evolve as real use cases become clearer.
