# ADR-0013: Put Metadata Parsing Behind a Provider Port

- **Status:** Accepted
- **Date:** 2026-08-03

## Context

MusicClean already has proven metadata extraction, including Mutagen-first
parsing and FFprobe fallback for parser edge cases such as high-rate WavPack.

Orion must preserve that reliability without coupling application/domain code
to parser libraries.

## Decision

Orion defines a `MetadataProvider` port returning normalized
`MetadataSnapshot` values.

The first adapter wraps the existing MusicClean metadata pipeline.

Parser provenance is represented explicitly with `MetadataParser` and optional
`parser_warning`.

## Consequences

- application code is parser-independent;
- proven fallback behavior is reused rather than rewritten immediately;
- future native Orion Mutagen and FFprobe adapters can replace the compatibility
  adapter behind the same contract;
- parser provenance is available for the future Evidence model.
