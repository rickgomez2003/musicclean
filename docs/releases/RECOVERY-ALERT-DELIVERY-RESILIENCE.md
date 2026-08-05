# Recovery Alert Delivery Resilience

Orion 0.6.49 separates recovery execution from webhook delivery.

## Privilege separation

`recovery-drill`:
- environment: `release-archive-export`
- OIDC enabled for archive access

`external-alert-delivery`:
- environment: `recovery-alert-delivery`
- no OIDC permission
- webhook secrets only

## Retry policy

Retry:
- HTTP 408
- HTTP 429
- HTTP 5xx
- network/timeout failures

Do not retry:
- other HTTP 4xx responses

Backoff is bounded exponential: 1, 2, 4, then at most 8 seconds.

Every delivery uses a deterministic `X-MusicClean-Delivery-ID` derived from
the canonical JSON payload and records attempt history in the delivery receipt.
