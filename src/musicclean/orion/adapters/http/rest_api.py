"""Framework-neutral REST adapter over OrionService."""

from __future__ import annotations

from musicclean.orion.application import (
    ApplicationError,
    ConflictError,
    NotFoundError,
    OrionService,
    QuarantineRequest,
    ReconcileRequest,
    RestoreRequest,
)
from musicclean.orion.application.service_models import ServiceExecutionResult
from musicclean.orion.shared import EntityId

from .transport import HttpRequest, HttpResponse, JsonObject


class RestApiAdapter:
    def __init__(self, service: OrionService) -> None:
        self._service = service

    def handle(self, request: HttpRequest) -> HttpResponse:
        try:
            return self._dispatch(request)
        except ValueError as exc:
            return self._error(400, "invalid_request", str(exc))
        except NotFoundError as exc:
            return self._error(404, "not_found", str(exc))
        except ConflictError as exc:
            return self._error(409, "conflict", str(exc))
        except ApplicationError as exc:
            return self._error(422, "application_error", str(exc))

    def _dispatch(self, request: HttpRequest) -> HttpResponse:
        method = request.method.upper().strip()
        path = request.path.rstrip("/") or "/"

        if method == "GET" and path == "/v1/health":
            health = self._service.health()
            return HttpResponse(
                200,
                {
                    "service": health.service,
                    "status": health.status,
                    "schema_version": health.schema_version,
                },
            )

        parts = [part for part in path.split("/") if part]
        if len(parts) != 4 or parts[:2] != ["v1", "action-plans"]:
            return self._error(404, "route_not_found", "route not found")

        plan_id = EntityId.parse(parts[2])
        operation = parts[3]
        if method != "POST":
            return HttpResponse(
                405,
                {"error": "method_not_allowed", "message": "POST required"},
                {"content-type": "application/json", "allow": "POST"},
            )

        if operation == "reconcile":
            result = self._service.reconcile(ReconcileRequest(plan_id))
            return HttpResponse(
                200,
                {
                    "finding_id": str(result.finding_id),
                    "action_plan_id": str(result.action_plan_id),
                    "status": result.status.value,
                    "proposed_action": result.proposed_action.value,
                    "detail": result.detail,
                },
            )

        body = self._require_body(request)
        if operation == "quarantine":
            execution = self._service.quarantine(
                QuarantineRequest(
                    action_plan_id=plan_id,
                    operator=self._required_text(body, "operator"),
                    idempotency_key=self._required_text(body, "idempotency_key"),
                    lease_owner=self._required_text(body, "lease_owner"),
                    lease_ttl_seconds=self._positive_int(body, "lease_ttl_seconds", 60),
                )
            )
            return HttpResponse(200, self._execution_body(execution))

        if operation == "restore":
            execution = self._service.restore(
                RestoreRequest(
                    action_plan_id=plan_id,
                    operator=self._required_text(body, "operator"),
                    idempotency_key=self._required_text(body, "idempotency_key"),
                    lease_owner=self._required_text(body, "lease_owner"),
                    lease_ttl_seconds=self._positive_int(
                        body,
                        "lease_ttl_seconds",
                        60,
                    ),
                )
            )
            return HttpResponse(200, self._execution_body(execution))

        return self._error(404, "route_not_found", "route not found")

    @staticmethod
    def _execution_body(result: ServiceExecutionResult) -> JsonObject:
        return {
            "execution_id": str(result.execution_id),
            "action_plan_id": str(result.action_plan_id),
            "kind": result.kind.value,
            "source_location": result.source_location,
            "target_location": result.target_location,
        }

    @staticmethod
    def _require_body(request: HttpRequest) -> JsonObject:
        if request.json_body is None:
            raise ValueError("JSON request body is required")
        return request.json_body

    @staticmethod
    def _required_text(body: JsonObject, key: str) -> str:
        value = body.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{key} must be a non-empty string")
        return value.strip()

    @staticmethod
    def _positive_int(body: JsonObject, key: str, default: int) -> int:
        value = body.get(key, default)
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError(f"{key} must be a positive integer")
        return value

    @staticmethod
    def _error(status: int, code: str, message: str) -> HttpResponse:
        return HttpResponse(status, {"error": code, "message": message})
