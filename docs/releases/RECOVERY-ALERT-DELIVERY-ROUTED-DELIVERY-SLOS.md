# Recovery Alert Delivery Routed Delivery SLOs

Orion 0.6.58 adds policy-driven service-level objectives for routed recovery
alert delivery.

The SLO evaluator consumes routed-delivery observability evidence and produces
PASS, WARN, or FAIL metric results for success rate, retry rate, average
attempts, average latency, terminal HTTP failures, and transport failures.

A minimum-sample gate marks whether the report is authoritative. Structured JSON
and Markdown summary evidence are retained with the recovery drill artifacts.

## History and trends in 0.6.59

0.6.59 retains bounded routed-delivery SLO evidence and classifies per-metric trends as improving, stable, worsening, or insufficient.
