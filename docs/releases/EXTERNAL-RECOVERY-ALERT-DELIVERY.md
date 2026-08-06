# External Recovery Alert Delivery

External recovery alerts use a generic HTTPS webhook with HMAC-SHA256 signing.

Delivery runs in the privilege-separated `external-alert-delivery` job using
the protected `recovery-alert-delivery` GitHub Environment.

0.6.50 adds delivery outcome, retry, failure classification, success-rate, and
latency observability derived from delivery receipts and prior artifacts.
Secret values and destination URLs are excluded from observability evidence.
