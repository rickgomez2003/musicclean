# ADR-0006: Keep Core Domain Entities Small and Relationship-Oriented

- **Status:** Accepted
- **Date:** 2026-08-03

## Context

A naive object graph such as Album -> list[Edition] -> list[Disc] ->
list[Track] forces large portions of a collection into memory and couples
domain construction to persistence loading behavior.

## Decision

Core Orion entities:

- have stable `EntityId` identities;
- contain local attributes and invariants;
- represent cross-entity relationships with IDs;
- do not require child collections to be eagerly embedded;
- remain independent of repositories and ORM types.

The first entity set is:

- Library
- Artist
- Album
- Edition
- Disc
- Recording
- TrackAppearance
- AudioFile

`AudioFile.recording_id` is optional because discovery can precede identity
resolution.

## Consequences

### Positive

- predictable memory behavior for large libraries;
- clean persistence mapping;
- easier unit testing;
- domain objects do not require an ORM session;
- partially-known libraries can be represented honestly.

### Tradeoffs

- application services/repositories must resolve relationships;
- convenience traversals require explicit queries;
- later aggregate boundaries must be designed deliberately rather than inferred
  from object nesting.
