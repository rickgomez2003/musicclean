# Book 05 — Service Contracts

**Status:** Active specification

## Persistence

Repository and UnitOfWork ports define persistence needs.

## Filesystem

`FilesystemObserver` yields lightweight filesystem observations.

## Metadata

`MetadataProvider` reads a path and returns a normalized `MetadataSnapshot`.

The contract deliberately exposes parser provenance but no Mutagen/FFprobe
objects, subprocess details, or parser-specific exceptions.
