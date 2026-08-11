# Recovery Alert Delivery Routed SLO Alert Delivery Routed Delivery SLOs

Orion 0.6.72 adds policy-driven, sample-gated SLO evaluation for routed SLO
alert-delivery routed delivery.

The SLO layer evaluates delivery success rate, retry rate, average attempts,
and transport failure rate, emits structured JSON evidence and a GitHub Actions
summary, and keeps all persisted evidence secret-safe.

## Routed-delivery SLO history and trends in 0.6.73

0.6.73 retains bounded SLO history and analyzes improving, worsening, stable, or insufficient-sample behavior without mutating delivery state.
