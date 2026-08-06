# Recovery Alert Delivery Resilience

Orion separates recovery execution from webhook delivery.

The dedicated delivery job uses the `recovery-alert-delivery` environment,
read-only repository permissions, and no OIDC write permission.

Retry semantics remain:

- retry HTTP 408;
- retry HTTP 429;
- retry HTTP 5xx;
- retry network and timeout failures;
- do not retry other HTTP 4xx responses.

0.6.50 adds artifact-based observability around this resilient delivery path.
