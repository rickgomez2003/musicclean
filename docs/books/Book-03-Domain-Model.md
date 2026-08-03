# Book 03 — Domain Model

**Status:** Active specification

## Purpose

Define Orion's music-domain language without coupling business concepts to the
filesystem, database, media parsers, or user interfaces.

## Core entities

### Library
A managed collection. Storage roots are configuration/infrastructure concerns
and are not Library identity.

### Artist
A credited creator or performer.

### Album
An abstract release concept independent of a particular publication.

### Edition
A specific published version of an Album.

### Disc
A physical or logical carrier within an Edition.

### Recording
A recorded performance independent of edition and file representation.

### TrackAppearance
The placement of a Recording on a Disc/Edition.

### AudioFile
A concrete digital representation at a mutable location. It may be discovered
before Orion knows which Recording it represents.

## Identity and relationships

Every entity uses a stable `EntityId`. Relationships are represented by IDs,
not mandatory nested object graphs.

This is intentional:

```text
Album
  id

Edition
  id
  album_id

Disc
  id
  edition_id

TrackAppearance
  id
  disc_id
  recording_id
```

Repositories and application use cases resolve relationships as needed.

## Invariants

The first domain model intentionally enforces only durable invariants:

- required human-readable names/titles are nonblank;
- Disc and TrackAppearance positions are positive integers;
- AudioFile location is nonblank;
- existing Shared Kernel value objects enforce their own ranges.

Orion does not assume every album has a year, every edition has a barcode,
every recording has an external identifier, or every file has already been
matched to a Recording.

## Immutability

Entities are frozen dataclasses in the initial model. State-changing use cases
will create replacement state or purpose-built domain operations rather than
allowing uncontrolled mutation.

## Future work

Artist/album/recording credit relationships, external identifiers, edition
release dates, recording identity evidence, and lifecycle state are deliberately
deferred until their invariants and use cases are specified.
