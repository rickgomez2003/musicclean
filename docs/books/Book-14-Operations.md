# Book 14 — Operations

0.6.32 establishes stable release operations.

The Release Candidate workflow now derives its version from the authoritative
MusicClean version source instead of repeating a hard-coded value throughout
the workflow. This removes the version-drift failure encountered when
development advanced from 0.6.30 to 0.6.31.

Stable operations also define patch/hotfix handling and immutable superseded
releases. GitHub-maintained checkout and Python setup actions are refreshed to
Node 24 compatible major versions.
