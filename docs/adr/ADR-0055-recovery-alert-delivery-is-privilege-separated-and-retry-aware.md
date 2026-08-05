# ADR-0055: Recovery Alert Delivery Is Privilege-Separated and Retry-Aware

- **Status:** Accepted
- **Date:** 2026-08-05

External recovery alert delivery runs in a dedicated workflow job and protected
GitHub Environment.

The delivery job has no OIDC write permission and cannot access the archive
recovery environment. Recovery produces a short-lived alert artifact that is
downloaded by the delivery job.

Retry policy distinguishes transient from terminal failures. HTTP 408, 429,
5xx, and network failures are retryable. Other 4xx responses are terminal.
Each payload receives a deterministic SHA-256 delivery identifier.
