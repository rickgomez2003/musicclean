# Book 12 — REST API

**Status:** Active specification

Initial routes:

- `GET /v1/health`
- `POST /v1/action-plans/{id}/quarantine`
- `POST /v1/action-plans/{id}/restore`
- `POST /v1/action-plans/{id}/reconcile`

The REST adapter maps transport concerns to `OrionService` and never accesses
SQLite, repositories, UnitOfWork, or the filesystem directly.

Error mapping:

- 400 invalid request
- 404 missing route/resource
- 405 unsupported method
- 409 state/idempotency/lease conflict
- 422 other application rejection
