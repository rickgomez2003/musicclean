"""FastAPI-only transport models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ActionRequestBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operator: str = Field(min_length=1)
    idempotency_key: str = Field(min_length=1)
    lease_owner: str = Field(min_length=1)
    lease_ttl_seconds: int = Field(default=60, gt=0)
