# Recovery Alert Delivery Routed SLO Alert Delivery Routed Delivery Observability

Orion 0.6.71 adds bounded, secret-safe observability for resilient routed SLO
alert-delivery delivery.

The observability artifact summarizes delivery outcome, route, attempt/retry
counts, terminal HTTP status, failure classification, deterministic delivery
ID, and bounded per-attempt status evidence. External export remains disabled.

## Routed-delivery SLOs in 0.6.72

0.6.72 adds policy-driven SLO evaluation over the bounded routed-delivery observability evidence introduced in 0.6.71.
