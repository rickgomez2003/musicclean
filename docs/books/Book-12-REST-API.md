# Book 12 — REST API

**Status:** Active specification

## Layering

```text
ASGI / FastAPI
      ↓
RestApiAdapter
      ↓
OrionService
      ↓
Application
      ↓
Ports / Adapters
```

## Version 1 routes

- `GET /v1/health`
- `POST /v1/action-plans/{action_plan_id}/quarantine`
- `POST /v1/action-plans/{action_plan_id}/restore`
- `POST /v1/action-plans/{action_plan_id}/reconcile`

## OpenAPI

The FastAPI host exposes:

- `/openapi.json`
- `/docs`
- `/redoc`

OpenAPI describes only the HTTP contract. Business rules remain behind
`RestApiAdapter` and `OrionService`.

## Hosting

The ASGI app is created with `create_fastapi_app(service)`.

Production process management and full bootstrap wiring are intentionally
separate from the host adapter.
