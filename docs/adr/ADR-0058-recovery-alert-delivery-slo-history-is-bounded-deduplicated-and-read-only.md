# ADR-0058: Recovery Alert Delivery SLO History Is Bounded, Deduplicated, and Read-Only

- **Status:** Accepted
- **Date:** 2026-08-06

Recovery alert delivery SLO history is assembled from retained workflow
artifacts. History is deduplicated, bounded to 52 records, and used only for
read-only trend evaluation.
