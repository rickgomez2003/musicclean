# ADR-0088: Routed SLO Alert Delivery Routed Delivery Routed Delivery SLO Routing Is Policy-Driven and Provider-Neutral

- **Status:** Accepted
- **Date:** 2026-08-12

Orion 0.6.82 converts provider-neutral routed-delivery SLO alert evidence into a logical route.

No-alert and non-authoritative evidence route to `none`, advisory alerts route to `operations`, and critical or escalated alerts route to `incident_response`.

This milestone performs logical routing only. External delivery remains disabled, and routing evidence remains secret-safe and provider-neutral.
