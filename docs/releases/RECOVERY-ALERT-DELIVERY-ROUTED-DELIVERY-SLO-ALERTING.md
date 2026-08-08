# Recovery Alert Delivery Routed Delivery SLO Alerting

Orion 0.6.60 adds provider-neutral alert decisions for routed recovery alert
delivery SLO evidence. It consumes current SLO status, trend evidence, and
bounded history, producing NONE, ADVISORY, CRITICAL, or ESCALATED severity.

## Escalation and routing in 0.6.61

0.6.61 consumes provider-neutral SLO alert evidence and produces a policy-driven logical route without performing external delivery.
