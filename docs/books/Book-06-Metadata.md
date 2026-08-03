# Book 06 — Metadata

**Status:** Active specification

## Purpose

Metadata parsing is an infrastructure capability exposed to Orion through a
stable provider port.

## Contract

`MetadataProvider.read(Path) -> MetadataSnapshot`

`MetadataSnapshot` contains normalized technical/tag values plus parser
provenance.

## Parser provenance

Current parser labels:

- Mutagen
- FFprobe
- Unknown

A parser warning may explain fallback or partial-recovery behavior.

## Initial adapter

`LegacyMetadataProvider` wraps MusicClean's already-proven metadata extraction
pipeline. This intentionally reuses the working Mutagen/FFprobe fallback rather
than rewriting it during architectural migration.

## Dependency rule

Application/domain code must not import Mutagen, subprocess FFprobe handling, or
legacy metadata implementation details.

## Future

A later milestone may split the compatibility adapter into native Orion
providers:

```text
CompositeMetadataProvider
    |
    +-- MutagenMetadataProvider
    +-- FFprobeMetadataProvider
```

The Evidence layer will record provider, algorithm version, timestamp, and
parser warnings.
