# Recovery Alert Delivery Routed SLO Alert Delivery Routed Delivery Resilience

Orion 0.6.70 adds bounded retry resilience to routed SLO alert-delivery
webhooks.

Retries are limited by policy, retryable HTTP statuses and transport failures
are explicit, backoff is bounded, delivery IDs are preserved across attempts,
and final receipts remain secret-safe.
