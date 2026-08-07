# Recovery Alert Delivery Routed Delivery Resilience

Orion 0.6.56 adds bounded retry behavior to route-specific recovery alert
delivery.

The resilience policy controls maximum attempts, exponential backoff, retryable
HTTP status codes, server-error retry behavior, and transport retries.

The selected route and deterministic delivery ID remain stable across retries,
and each delivery receipt records an ordered attempt history.
