# ADR-0087: Routed SLO Alert Delivery Routed Delivery Routed Delivery SLO Alerting Is Provider-Neutral

- **Status:** Accepted
- **Date:** 2026-08-12

Orion 0.6.81 converts routed-delivery SLO state and trend evidence into a bounded, provider-neutral alert object.

PASS produces no alert, WARN produces an advisory alert, FAIL produces a critical alert, and insufficient evidence remains non-authoritative. A worsening trend can elevate an advisory condition, while repeated non-passing observations can produce an escalated alert state.

External delivery remains disabled in this milestone. Alert evidence stays secret-safe and contains no endpoint, credential, signature, authorization, webhook, or request-header material.
