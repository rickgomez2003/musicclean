# Book 06 — Metadata

**Status:** Active specification

Metadata parsing is exposed through `MetadataProvider`.

0.6.8 adds the next stage: normalized `MetadataSnapshot` fields are converted
into persistent `EvidenceRecord` observations attached to an AudioFile.

Parser/provider warning information is preserved in Evidence provenance so a
future Knowledge rule can distinguish direct parsing from fallback recovery.
