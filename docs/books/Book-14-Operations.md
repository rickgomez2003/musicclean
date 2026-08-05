# Book 14 — Operations

0.6.38 introduces release promotion and explicit release channels.

Controlled release creation remains responsible for building, validating,
checksumming, SBOM generation, attestations, and publication.

Promotion operates only on an already-published GitHub Release:

- `preview` keeps the release marked as prerelease and not latest;
- `stable` clears prerelease status and marks the release as latest.

Promotion references GitHub Environments named `release-preview` and
`release-stable`, allowing repository owners to add approval or deployment
protection rules without coupling those rules to artifact creation.

The critical invariant is that promotion changes metadata only. It never
rebuilds or replaces release artifacts.
