# ADR-0071: Routed SLO Alert Delivery SLOs Are Policy-Driven and Sample-Gated

- **Status:** Accepted
- **Date:** 2026-08-08

Orion 0.6.65 introduces policy-driven service-level objectives for routed
recovery SLO alert delivery.

The SLO layer evaluates delivery success, retry rate, average attempts, and
transport failure rate. Results are sample-gated so insufficient evidence is
explicitly non-authoritative.

Generated evidence remains secret-safe and contains no endpoint URLs, HMAC
secrets, signatures, authorization material, webhook URLs, or request headers.
