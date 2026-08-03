# ADR-0011: Application Use Cases Depend on Ports and a UnitOfWork Factory

- **Status:** Accepted
- **Date:** 2026-08-03

## Context

Application operations need a fresh transactional boundary but must remain
independent of the concrete persistence adapter.

Passing an already-open UnitOfWork makes ownership and nesting ambiguous.

## Decision

Application use cases depend on `UnitOfWorkFactory`, a callable port that
creates a fresh `UnitOfWork` for one operation.

The first use cases are:

- create a Library;
- register/refresh an AudioFile;
- list Editions for an Album.

Application modules may depend on:

- Orion domain entities;
- Shared Kernel value objects;
- ports;
- application-specific errors and command/query DTOs.

They may not import concrete SQLite adapters.

## Consequences

- transaction ownership is clear;
- use cases are adapter-independent;
- tests can use in-memory or SQLite-backed factories;
- each operation has an explicit persistence boundary.
