# Book 14 — Operations

0.6.30 establishes the first controlled release procedure.

A release tag may be created only from the exact merged commit that has passed
release-candidate validation.

The controlled release procedure requires:

- one authoritative version;
- a clean merged repository state;
- successful release-candidate validation;
- an annotated semantic version tag;
- immutable published tags;
- release artifact verification;
- rollback by forward-fixing to a new version rather than moving an old tag.
