# ADR-0072: Routed SLO Alert Delivery SLO History Is Bounded, Deduplicated, and Read-Only

- **Status:** Accepted
- **Date:** 2026-08-08

Orion 0.6.66 adds historical SLO tracking and trend analysis for routed recovery
SLO alert delivery.

History is bounded to 52 records, deduplicated by stable report fingerprint,
and treated as read-only operational evidence. Trend analysis uses recent and
baseline windows with a minimum authoritative sample gate.

History and trend evidence must remain secret-safe.
