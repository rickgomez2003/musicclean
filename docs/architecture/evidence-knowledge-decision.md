# Evidence → Knowledge → Decision

## Evidence
Raw observations with provider/analyzer and algorithm-version provenance: codec, sample rate, hashes, fingerprints, identifiers, loudness, artwork properties.

## Knowledge
Inferred facts supported by evidence: byte-identical, likely same mastering, incomplete release, inconsistent metadata, likely upsampled.

## Decision
Proposed action: KEEP, ARCHIVE, QUARANTINE, REANALYZE, REPAIR_METADATA, FETCH_ARTWORK, IGNORE.

A Decision records subject, action, confidence, rationale, supporting knowledge, risk, alternatives, storage impact, engine versions, ruleset version, and timestamp. Decision generation never executes the mutation.
