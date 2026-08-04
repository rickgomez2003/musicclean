# ADR-0036: Controlled Releases Are Tagged Only From Validated Merged Commits

- **Status:** Accepted
- **Date:** 2026-08-04

A controlled MusicClean release tag may be created only from the exact merged
commit that has passed release-candidate validation.

The release sequence is:

1. prepare the release version on a feature branch;
2. pass local quality and artifact validation;
3. pass all pull-request checks, including `Orion Release Candidate`;
4. merge to `develop`;
5. confirm the merged commit and clean repository state;
6. confirm release-candidate validation for the merged version;
7. create an annotated semantic version tag on that exact commit;
8. push the tag to trigger the `Orion Release` workflow.

Tags are immutable release identifiers. A bad release is corrected with a new
version; an already-published tag is not silently moved.
