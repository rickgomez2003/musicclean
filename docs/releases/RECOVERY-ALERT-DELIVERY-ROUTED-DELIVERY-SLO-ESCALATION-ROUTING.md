# Recovery Alert Delivery Routed Delivery SLO Escalation & Routing

Orion 0.6.61 adds policy-driven, provider-neutral escalation and routing for
routed recovery alert delivery SLO alerts.

The routing layer maps NONE, ADVISORY, CRITICAL, and ESCALATED severities to
logical routes, preserves the source route context, emits structured route
evidence, and keeps external delivery disabled.

## Routed SLO alert delivery in 0.6.62

0.6.62 consumes the logical SLO route and performs route-specific signed webhook delivery with isolated credentials.
