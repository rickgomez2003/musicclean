# Book 14 — Operations

0.6.25 adds optional OpenTelemetry export over the provider-neutral telemetry
boundary.

Configuration:

- `MUSICCLEAN_ORION_OTEL_ENDPOINT`
- `MUSICCLEAN_ORION_OTEL_SERVICE_NAME`

OpenTelemetry dependencies remain optional. With no endpoint configured, Orion
does not import or initialize the OpenTelemetry SDK.

Install optional packages with:

`pip install -r requirements/orion-opentelemetry.txt`
