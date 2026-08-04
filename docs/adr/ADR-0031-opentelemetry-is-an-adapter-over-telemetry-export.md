# ADR-0031: OpenTelemetry Is an Adapter Over Telemetry Export

- **Status:** Accepted
- **Date:** 2026-08-04

OpenTelemetry is implemented as an adapter over Orion's provider-neutral
`TelemetryExporter` boundary.

Orion domain and application code do not depend on OpenTelemetry APIs, SDK
objects, OTLP payloads, or collector topology.

When configured, Orion converts telemetry events into short OpenTelemetry spans
and exports them through OTLP/HTTP.

OpenTelemetry remains optional. Orion must start and operate normally when the
optional OpenTelemetry packages are not installed and OTel is disabled.
