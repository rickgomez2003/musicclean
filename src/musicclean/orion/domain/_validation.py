"""Internal validation helpers for Orion domain entities."""

from musicclean.orion.shared import DomainValidationError


def require_text(value: str, field_name: str) -> str:
    """Return stripped text or raise when a required field is empty."""
    normalized = value.strip()
    if not normalized:
        raise DomainValidationError(f"{field_name} must not be empty")
    return normalized


def optional_text(value: str | None) -> str | None:
    """Normalize optional text, converting blank strings to None."""
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None
