# ADR-0069: Routed SLO Alert Delivery Retries Are Bounded and Idempotency-Aware

- **Status:** Accepted
- **Date:** 2026-08-08

Orion 0.6.63 adds bounded retries for retryable HTTP and transport failures.
Terminal HTTP failures do not retry. Deterministic delivery IDs are preserved
across attempts, and secret-safe attempt history is retained in receipt evidence.
