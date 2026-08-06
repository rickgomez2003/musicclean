# ADR-0056: Recovery Alert Delivery Observability Is Artifact-Based and Secret-Safe

- **Status:** Accepted
- **Date:** 2026-08-05

Recovery alert delivery observability is derived from delivery receipts and
prior delivery artifacts.

Observability records operational outcomes such as attempt count, retry count,
status code, failure class, delivery ID, sample count, success rate, and
latency when available.

Destination URLs, signing secrets, and other secret material are excluded from
observability evidence and summaries.
