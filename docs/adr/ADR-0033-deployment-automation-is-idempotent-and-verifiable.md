# ADR-0033: Deployment Automation Is Idempotent and Verifiable

- **Status:** Accepted
- **Date:** 2026-08-04

Deployment automation must be safe to rerun and must verify that Orion is
healthy before reporting success.

Automation wraps the existing 0.6.26 deployment artifacts and runtime
composition root.

Required properties:

- directory creation is idempotent;
- existing configuration is preserved;
- service definitions are updated explicitly;
- service restarts are deliberate;
- health verification is mandatory after startup/update;
- failures are reported rather than silently treated as success;
- domain and application layers remain deployment-neutral.
