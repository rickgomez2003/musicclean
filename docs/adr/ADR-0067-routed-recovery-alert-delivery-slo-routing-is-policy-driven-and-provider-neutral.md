# ADR-0067: Routed Recovery Alert Delivery SLO Routing Is Policy-Driven and Provider-Neutral

- **Status:** Accepted
- **Date:** 2026-08-08

Orion 0.6.61 maps provider-neutral routed-delivery SLO alerts to logical routes
using repository policy.

NONE routes to no destination, ADVISORY routes to operations, and CRITICAL or
ESCALATED alerts route to incident-response. Escalated alerts may override the
normal severity mapping.

The routing layer preserves source alert context but performs no network
delivery. External delivery remains disabled.
