"""HTTP transport models for Orion."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

JsonObject = dict[str, Any]


@dataclass(frozen=True, slots=True)
class HttpRequest:
    method: str
    path: str
    json_body: JsonObject | None = None
    headers: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class HttpResponse:
    status_code: int
    body: JsonObject
    headers: dict[str, str] = field(default_factory=lambda: {"content-type": "application/json"})
