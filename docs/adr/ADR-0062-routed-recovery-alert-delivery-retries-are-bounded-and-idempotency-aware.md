# ADR-0062: Routed Recovery Alert Delivery Retries Are Bounded and Idempotency-Aware

- **Status:** Accepted
- **Date:** 2026-08-07

Orion 0.6.56 makes routed recovery alert delivery retry-aware.

Retries are bounded, use exponential backoff, preserve the selected route, and
preserve the deterministic delivery ID across attempts. Terminal HTTP failures
do not retry. Retryable HTTP and transport failures may retry according to
policy.

Attempt history is retained in the secret-safe delivery receipt.
