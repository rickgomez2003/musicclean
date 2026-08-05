# Book 14 — Operations

0.6.37 adds a conservative automated dependency merge policy.

Dependabot PATCH and MINOR version-update pull requests targeting `develop`
may have GitHub auto-merge enabled automatically. MAJOR dependency updates
remain manual.

The automation uses squash auto-merge and never uses an administrative bypass.
GitHub branch protection/rulesets remain the actual merge enforcement boundary.

Before enabling this feature operationally:

- enable repository **Allow auto-merge**;
- require the intended CI/security checks on `develop`;
- keep Dependency Review and Python Runtime Audit authoritative.

Dependency proposal, security evaluation, and merge authorization remain
separate responsibilities.
