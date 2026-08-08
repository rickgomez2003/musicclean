# Recovery Alert Delivery Routed SLO Alert Delivery Resilience

Orion 0.6.63 adds bounded retries, exponential backoff, deterministic delivery
IDs, and secret-safe per-attempt evidence to routed SLO alert delivery.

## Observability in 0.6.64

0.6.64 converts secret-safe delivery receipts into bounded operational evidence.
