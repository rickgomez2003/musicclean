# Book 14 — Operations

0.6.52 adds Recovery Alert Delivery SLO History & Trends.

History is read-only, artifact-based, deduplicated, capped at 52 records, and
published to the GitHub Actions summary.\n\n## Recovery Alert Delivery SLO Alerting (0.6.53)\n\n0.6.53 emits provider-neutral alert decisions from delivery SLO and trend evidence.\n\n\n## Recovery Alert Delivery SLO Escalation & Routing (0.6.54)\n\n0.6.54 converts provider-neutral SLO alert evidence into a provider-neutral routing decision.\n

## Recovery Alert Delivery Routed Delivery (0.6.55)

0.6.55 delivers route decisions through route-specific signed HTTPS webhooks and emits secret-safe receipts.

## Recovery Alert Delivery Routed Delivery Resilience (0.6.56)

0.6.56 adds bounded retries, exponential backoff, stable delivery IDs, and attempt history to route-specific recovery alert delivery.

## Recovery Alert Delivery Routed Delivery Observability (0.6.57)

0.6.57 aggregates bounded routed-delivery receipts into success, retry, attempt, route, failure-class, and latency observability while excluding destination and secret material.

## Recovery Alert Delivery Routed Delivery SLOs (0.6.58)

0.6.58 evaluates routed-delivery observability against sample-gated, policy-driven service-level objectives.

## Recovery Alert Delivery Routed Delivery SLO History & Trends (0.6.59)

0.6.59 adds bounded, deduplicated routed-delivery SLO history and sample-gated short/long-window trend analysis.
