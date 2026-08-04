# ADR-0026: HTTP Host Is an Adapter over the REST Contract

- **Status:** Accepted
- **Date:** 2026-08-04

## Decision

FastAPI is introduced only in the HTTP-host adapter.

The host owns:

- ASGI integration;
- OpenAPI generation;
- Swagger UI and ReDoc;
- framework request validation;
- conversion between FastAPI requests and `HttpRequest`;
- conversion from `HttpResponse` to framework responses.

The host does not bypass `RestApiAdapter` or `OrionService`.

## Dependency boundary

FastAPI, Uvicorn, Pydantic transport models, and HTTP test-client dependencies
remain outside the domain and application layers.
