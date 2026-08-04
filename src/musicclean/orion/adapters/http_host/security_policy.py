"""Runtime HTTP security policy."""

from __future__ import annotations

import hmac
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RuntimeSecurityPolicy:
    api_key: str | None
    public_health: bool = True
    max_request_bytes: int = 1_048_576
    allowed_origins: tuple[str, ...] = ()
    allowed_hosts: tuple[str, ...] = ("127.0.0.1", "localhost")

    def __post_init__(self) -> None:
        if self.api_key is not None and not self.api_key.strip():
            raise ValueError("api_key cannot be blank")
        if self.max_request_bytes <= 0:
            raise ValueError("max_request_bytes must be positive")
        if not self.allowed_hosts:
            raise ValueError("allowed_hosts cannot be empty")

    @property
    def authentication_enabled(self) -> bool:
        return self.api_key is not None

    def authenticates(self, candidate: str | None) -> bool:
        if self.api_key is None:
            return True
        if candidate is None:
            return False
        return hmac.compare_digest(candidate, self.api_key)
