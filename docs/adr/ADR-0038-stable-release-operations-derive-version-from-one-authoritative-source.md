# ADR-0038: Stable Release Operations Derive Version From One Authoritative Source

- **Status:** Accepted
- **Date:** 2026-08-04

`src/musicclean/version.py` is the authoritative version source.

Release Candidate automation derives the version at runtime rather than
embedding it in repeated commands, artifact names, or installation paths.

Published-release verification may intentionally retain a historical version
because it verifies an immutable release that already exists.

GitHub-maintained JavaScript actions are kept on Node 24 compatible majors.
