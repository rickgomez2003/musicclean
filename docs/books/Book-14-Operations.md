# Book 14 — Operations

0.6.41 adds release retention and archival.

Verified release audit evidence can now be transformed into a deterministic
archive bundle containing the original evidence files, an archive manifest, and
SHA-256 integrity metadata.

Two retention classes are defined:

- operational: at least 90 days;
- long-term: at least 2555 days.

GitHub Actions retains the generated archive artifact for 90 days. Long-term
archives therefore require export to an external durable records system before
that temporary artifact expires.

The archive workflow is read-only with respect to published releases.
