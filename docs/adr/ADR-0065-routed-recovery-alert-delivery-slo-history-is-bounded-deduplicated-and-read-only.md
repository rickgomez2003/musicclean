# ADR-0065: Routed Recovery Alert Delivery SLO History Is Bounded, Deduplicated, and Read-Only

- **Status:** Accepted
- **Date:** 2026-08-07

Orion 0.6.59 adds bounded historical tracking and trend analysis for routed
recovery alert delivery SLO evidence.

Historical reports are deduplicated and capped by policy. Trend analysis uses
short and long windows with minimum-sample gating before classifying delivery
health as improving, stable, or worsening.

Historical collection is read-only and secret-safe. It does not add repository
write permissions, release mutation privileges, destination information, or
secret material.
