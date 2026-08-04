# ADR-0030: Telemetry Export Is Provider-Neutral

- **Status:** Accepted
- **Date:** 2026-08-04

Orion exports operational telemetry through a provider-neutral exporter
protocol.

The runtime emits stable telemetry events and does not depend on vendor-specific
SDKs or payload formats.

Exporter failures are isolated and must never break request processing.

The first concrete exporter is append-only JSON Lines. Future adapters may
target OpenTelemetry, Prometheus-derived systems, Loki, Splunk, or other
backends without changing Orion domain/application code.
