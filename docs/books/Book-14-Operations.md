# Book 14 — Operations

0.6.26 adds repeatable runtime packaging and deployment artifacts.

Supported deployment wrappers include:

- Docker;
- Linux systemd;
- Windows PowerShell service wrapper.

All deployment forms invoke the same runtime composition root:

`python -m musicclean.orion.runtime`

Production runtime dependencies are available through the `orion-runtime`
optional package extra. OpenTelemetry remains independently optional.

Deployment configuration is environment-driven. Writable database, log, and
telemetry locations must be explicitly provisioned for the service identity.
