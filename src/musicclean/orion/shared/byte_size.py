"""Byte-size value object."""

from __future__ import annotations

from dataclasses import dataclass

from musicclean.orion.shared.errors import DomainValidationError


@dataclass(frozen=True, slots=True, order=True)
class ByteSize:
    """Non-negative size in bytes."""

    bytes: int

    def __post_init__(self) -> None:
        if isinstance(self.bytes, bool) or self.bytes < 0:
            raise DomainValidationError("byte size must be a non-negative integer")

    @property
    def kib(self) -> float:
        return self.bytes / 1024

    @property
    def mib(self) -> float:
        return self.bytes / (1024**2)

    @property
    def gib(self) -> float:
        return self.bytes / (1024**3)
