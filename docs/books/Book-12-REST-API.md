# Book 12 — REST API

HTTP security is enforced before requests reach `RestApiAdapter`.

Protected requests use:

`X-API-Key: <secret>`

The health endpoint may remain public for monitoring. Responses include
`nosniff`, `DENY` frame protection, `no-referrer`, and `no-store`.
