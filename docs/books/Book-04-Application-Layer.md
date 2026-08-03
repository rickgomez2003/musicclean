# Book 04 — Application Layer

**Status:** Active specification

## Purpose

The Application Layer coordinates Orion domain behavior through ports. It owns
use-case orchestration and transaction boundaries, not infrastructure details.

## Dependency direction

```text
Interface / CLI / API
        |
        v
Application Use Case
        |
        +--> Domain
        +--> Shared Kernel
        +--> Ports
                 |
                 v
             Adapter
```

Application code does not import SQLite, FFmpeg, Mutagen, MusicBrainz clients,
or UI frameworks.

## Unit-of-work ownership

A use case receives a `UnitOfWorkFactory`. Each invocation creates and owns a
fresh UnitOfWork.

This avoids leaking adapter connection lifetimes into callers.

## First commands and queries

### CreateLibrary

Creates a normalized `Library` and rejects a case-insensitive duplicate name.

### RegisterAudioFile

Registers a newly discovered file or refreshes an existing location while
preserving stable AudioFile identity.

If a Recording association is supplied, the Recording must exist.

### ListAlbumEditions

Returns all known Editions for an existing Album.

## Error model

Use-case failures use application-specific exceptions:

- `ConflictError`
- `NotFoundError`

Domain invariant failures continue to use domain/shared validation errors.

## Command/query objects

Input values are represented as small immutable dataclasses. This keeps
interface-specific parsing outside the application use case and gives later
CLI/API layers stable input contracts.

## Next work

Future increments will introduce synchronization-oriented use cases, richer
queries, event publication, and application result/view models where needed.
