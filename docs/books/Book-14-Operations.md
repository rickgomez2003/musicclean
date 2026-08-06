# Book 14 — Operations

0.6.50 adds Recovery Alert Delivery Observability.

The delivery job now derives operational metrics from its current receipt and
up to 52 prior delivery artifacts. GitHub Actions summaries show delivery
outcome, attempts, retries, HTTP status, failure class, sample count, and
historical success rate.

Observability is artifact-based and excludes webhook destinations, signing
secrets, and other secret material.
