"""Shared Orion exception hierarchy."""


class OrionError(Exception):
    """Base exception for Orion-specific failures."""


class DomainValidationError(OrionError, ValueError):
    """Raised when a domain value violates an invariant."""


class InvalidIdentifierError(DomainValidationError):
    """Raised when a stable identifier cannot be parsed or validated."""
