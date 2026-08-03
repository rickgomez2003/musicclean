"""Foundational audio technical value objects."""

from __future__ import annotations

from dataclasses import dataclass

from musicclean.orion.shared.errors import DomainValidationError


@dataclass(frozen=True, slots=True, order=True)
class SampleRate:
    """Audio sample rate in hertz."""

    hz: int

    def __post_init__(self) -> None:
        if isinstance(self.hz, bool) or self.hz <= 0:
            raise DomainValidationError("sample rate must be a positive integer")


@dataclass(frozen=True, slots=True, order=True)
class BitDepth:
    """Integer PCM bit depth."""

    bits: int

    def __post_init__(self) -> None:
        if isinstance(self.bits, bool) or self.bits <= 0:
            raise DomainValidationError("bit depth must be a positive integer")
