# Stable Release Operations

Stable release operations begin with development version 0.6.32.

## Version authority

`src/musicclean/version.py` is authoritative. Release Candidate automation
discovers the value once and propagates it throughout the candidate pipeline.

## Patch and hotfix policy

A published release is immutable. A production defect is corrected with a new
patch version through the same candidate, controlled-release, and post-release
verification sequence.

1. Branch from the appropriate supported baseline.
2. Apply the smallest safe correction.
3. Increment the patch version.
4. Pass Release Candidate validation.
5. Merge the validated change.
6. Create an annotated tag on the exact merged commit.
7. Verify the published artifacts.

Never move or reuse an existing published tag.

## Superseded releases

Superseded releases remain auditable. Release notes identify the preferred
replacement version when appropriate.
