# Recovery Alert Delivery Routed SLO Alert Delivery Routed Delivery SLO History & Trends

Orion 0.6.73 adds bounded, deduplicated history and minimum-sample-gated trend
analysis for routed SLO alert-delivery routed-delivery SLO evidence.

The history layer retains a bounded set of secret-safe SLO records keyed by
deterministic delivery ID. Trend analysis evaluates success rate, retry rate,
average delivery attempts, and transport failure rate for improving,
worsening, stable, or insufficient-sample behavior.
