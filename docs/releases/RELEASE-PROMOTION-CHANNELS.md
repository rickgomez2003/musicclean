# Release Promotion & Channels

## Channels

MusicClean defines two release channels.

### Preview

Environment: `release-preview`

A preview release:

- is marked as a GitHub prerelease;
- is not marked as the latest release;
- uses the exact artifacts created by the controlled release workflow.

### Stable

Environment: `release-stable`

A stable release:

- is not marked as a prerelease;
- is marked as GitHub's latest release;
- uses the exact artifacts created by the controlled release workflow.

## Promotion workflow

Use **Orion Release Promotion** from GitHub Actions and provide:

- an existing published release tag;
- `preview` or `stable`.

The workflow verifies the published release before editing release metadata.

It does not:

- rebuild packages;
- regenerate checksums;
- regenerate the SBOM;
- regenerate attestations;
- create a new release.

## GitHub Environments

Create the following repository environments:

- `release-preview`
- `release-stable`

GitHub Environments can enforce deployment protection rules before the
promotion job executes. For stable promotion, consider required reviewer
approval and disabling administrator bypass where supported by repository
policy.

## Rollback

Promotion metadata can be changed again by rerunning the promotion workflow
for the same immutable release tag.

Artifact rollback is a separate release operation and must never replace
artifacts attached to an existing immutable controlled release.
