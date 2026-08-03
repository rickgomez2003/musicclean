"""Application-layer exceptions for Orion."""


class ApplicationError(Exception):
    """Base exception for application use-case failures."""


class ConflictError(ApplicationError):
    """Raised when a command conflicts with existing persisted state."""


class NotFoundError(ApplicationError):
    """Raised when a requested domain entity does not exist."""
