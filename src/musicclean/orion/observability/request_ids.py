"""Request/correlation identifier handling."""

from __future__ import annotations

import re
from uuid import uuid4

_ALLOWED = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


def normalize_request_id(candidate: str | None) -> str:
    if candidate is not None:
        value = candidate.strip()
        if _ALLOWED.fullmatch(value):
            return value
    return uuid4().hex
