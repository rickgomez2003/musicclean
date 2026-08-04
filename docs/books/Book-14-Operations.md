# Book 14 — Operations

0.6.28 adds release engineering around the packaged Orion runtime.

Release engineering now provides:

- one package/runtime version source;
- semantic release-tag validation;
- wheel and source-distribution builds;
- metadata verification;
- SHA-256 artifact checksums;
- built-wheel smoke testing;
- GitHub Release automation.

Release tags must match the authoritative package version before artifacts can
be published as a GitHub Release.
