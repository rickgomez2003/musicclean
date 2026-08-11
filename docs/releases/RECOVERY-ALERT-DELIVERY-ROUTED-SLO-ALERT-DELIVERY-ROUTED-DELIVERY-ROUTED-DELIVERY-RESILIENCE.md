# Recovery Alert Delivery Routed SLO Alert Delivery Routed Delivery Routed Delivery Resilience

Orion 0.6.77 adds bounded, idempotency-aware retry behavior to routed SLO
alert-delivery routed-delivery webhook delivery.

Retryable HTTP failures and transport failures may be retried according to
policy. Exponential backoff is capped, delivery IDs remain stable across
attempts, and secret-safe per-attempt evidence is retained within a strict
bound.

## Routed-delivery observability in 0.6.78

0.6.78 summarizes terminal state, attempts, retries, HTTP status, failure classification, and bounded attempt evidence without retaining request material.
