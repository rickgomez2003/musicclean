# ADR-0086: Routed SLO Alert Delivery Routed Delivery Routed Delivery SLO History Is Bounded, Deduplicated, and Read-Only

- **Status:** Accepted
- **Date:** 2026-08-12

Orion 0.6.80 adds bounded historical SLO evidence and trend analysis for routed delivery.

History retention is capped, entries are deterministically deduplicated, and the history path is read-only with respect to external systems. Trend analysis covers delivery success rate, retry rate, average attempts, and transport-failure rate.

Trend classifications are IMPROVING, STABLE, WORSENING, and INSUFFICIENT_HISTORY. Evidence remains provider-neutral and secret-safe, and external export stays disabled.
