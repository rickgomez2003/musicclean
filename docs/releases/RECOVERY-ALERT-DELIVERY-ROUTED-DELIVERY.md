# Recovery Alert Delivery Routed Delivery

Orion 0.6.55 adds route-specific external delivery for recovery alert delivery
SLO alerts.

The provider-neutral route decision selects either the operations route or the
incident-response route. Each route uses its own HTTPS webhook URL and HMAC
secret.

The delivery tool emits a secret-safe receipt containing route, severity,
status, elapsed time, deterministic delivery ID, and failure classification.

## Resilience in 0.6.56

0.6.56 adds bounded retry behavior while preserving route selection and deterministic delivery identity across attempts.
