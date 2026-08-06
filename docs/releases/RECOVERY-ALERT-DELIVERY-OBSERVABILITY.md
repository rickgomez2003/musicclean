# Recovery Alert Delivery Observability

Orion 0.6.50 adds delivery-level observability to the recovery alert pipeline.

Recorded signals include:

- delivery outcome;
- attempt count;
- retry count;
- HTTP status code;
- failure classification;
- deterministic delivery ID;
- historical sample count;
- delivery success rate;
- latency when present in receipt evidence.

The workflow collects up to 52 prior delivery artifacts, builds bounded
observability evidence, publishes a GitHub Actions summary, and retains the
machine-readable evidence for 90 days.

Webhook destination URLs and signing secrets are never recorded.
