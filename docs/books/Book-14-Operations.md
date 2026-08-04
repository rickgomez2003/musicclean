# Book 14 — Operations

0.6.29 adds release-candidate validation from built artifacts.

Before a release tag is created, CI now proves that the candidate wheel and
source distribution are internally consistent and operational.

Validation includes:

- version and metadata checks;
- SHA-256 checksum coverage;
- clean-environment wheel installation;
- installed-package version verification;
- Orion startup from the installed wheel;
- `/v1/health` verification.

The release-candidate workflow does not publish artifacts as a GitHub Release.
