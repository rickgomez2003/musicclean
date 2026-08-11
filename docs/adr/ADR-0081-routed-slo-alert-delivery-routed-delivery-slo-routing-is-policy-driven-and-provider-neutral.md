# ADR-0081: Routed SLO Alert Delivery Routed Delivery SLO Routing Is Policy-Driven and Provider-Neutral

- **Status:** Accepted
- **Date:** 2026-08-11

Orion 0.6.75 adds policy-driven logical routing for routed SLO alert-delivery
routed-delivery SLO alerts.

No-alert and non-authoritative states route to `none`. Advisory alerts route to
`operations`. Critical and escalated alerts route to `incident-response`.

This layer remains provider-neutral and does not perform external delivery.
