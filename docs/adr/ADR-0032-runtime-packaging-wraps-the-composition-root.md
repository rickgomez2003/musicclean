# ADR-0032: Runtime Packaging Wraps the Composition Root

- **Status:** Accepted
- **Date:** 2026-08-04

Deployment artifacts launch the existing Orion runtime composition root rather
than rebuilding dependency wiring.

Container, Linux service, and Windows service wrappers configure the runtime
through environment variables and invoke:

`python -m musicclean.orion.runtime`

Deployment concerns remain outside domain and application layers.

Production packaging uses a dedicated `orion-runtime` dependency extra.
OpenTelemetry remains an optional, separately selectable extra.
