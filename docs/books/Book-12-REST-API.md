# Book 12 — REST API

HTTP requests are correlated with `X-Request-ID`.

A valid caller-provided ID is preserved. If absent or invalid, Orion generates
an opaque request ID and returns it on the response.

API keys and secret-bearing fields are never emitted in structured telemetry.
