# Release Rollback & Recovery

Rollback restores the stable channel to a previously published MusicClean
release when the current stable release must be withdrawn.

The **Orion Release Rollback** workflow requires `current_tag` and
`recovery_tag`. Both must already exist as published GitHub Releases.

Before any change, the workflow verifies both releases, rejects drafts, and
requires `current_tag` to be GitHub's current latest release.

The operation then demotes the current release to prerelease/non-latest,
promotes the recovery release to non-prerelease/latest, and verifies the final
GitHub release state.

Rollback never rebuilds artifacts, regenerates checksums/SBOMs/attestations,
deletes tags or releases, replaces assets, or uses administrative bypass.

After rollback, remediation follows the normal fix-forward release path with a
new version and new immutable tag.
