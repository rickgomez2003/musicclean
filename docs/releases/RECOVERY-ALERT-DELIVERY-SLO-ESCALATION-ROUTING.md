# Recovery Alert Delivery SLO Escalation & Routing

Orion 0.6.54 adds deterministic routing decisions for provider-neutral recovery
alert delivery SLO alerts.

Routes distinguish normal operations handling from incident-response
escalation. Repeated non-pass conditions and worsening critical conditions can
force the escalation route.

This milestone generates evidence only. It does not perform external delivery.

## Routed delivery in 0.6.55

0.6.55 consumes the route decision and performs route-specific signed delivery using separately configured operations and incident-response endpoints.
