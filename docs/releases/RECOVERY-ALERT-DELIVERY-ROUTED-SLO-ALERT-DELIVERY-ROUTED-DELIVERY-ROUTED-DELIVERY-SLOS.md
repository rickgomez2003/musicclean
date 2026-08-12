# Recovery Alert Delivery Routed SLO Alert Delivery Routed Delivery Routed Delivery SLOs

Orion 0.6.79 adds policy-driven, sample-gated SLO evaluation for routed-delivery observability evidence.

The SLO layer evaluates delivery success rate, retry rate, average attempts, and transport-failure rate. Insufficient samples produce a non-authoritative INSUFFICIENT_SAMPLES result rather than PASS or FAIL.
