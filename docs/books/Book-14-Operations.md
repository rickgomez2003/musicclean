# Book 14 — Operations

0.6.49 adds Recovery Alert Delivery Resilience.

Archive recovery remains in `release-archive-export` with AWS OIDC. External
notification delivery moves into a separate `recovery-alert-delivery`
environment with read-only repository permissions and no OIDC write access.

Transient delivery failures use bounded exponential backoff. Terminal 4xx
responses fail immediately. Delivery receipts include attempt history,
classification, and a deterministic delivery ID without storing destination
URLs or signing secrets.
