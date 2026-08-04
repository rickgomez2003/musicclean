# ADR-0029: Observability Is Correlated and Secret-Safe

Every externally initiated operation receives a correlation identifier.

Operational telemetry must include request IDs, method, path, status and duration,
while redacting credentials and secret-bearing fields. Domain and application
layers remain logging-backend neutral.
