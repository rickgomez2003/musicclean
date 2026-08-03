"""Deterministic Evidence-to-Knowledge inference rules."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from musicclean.orion.domain import (
    EvidenceKind,
    EvidenceRecord,
    KnowledgeFact,
    KnowledgeKind,
)
from musicclean.orion.shared import Confidence, EntityId


class KnowledgeRule(Protocol):
    """Contract for deterministic inference from Evidence."""

    @property
    def rule_id(self) -> str:
        """Stable identifier for the inference rule."""
        ...

    @property
    def rule_version(self) -> str:
        """Version of the inference algorithm."""
        ...

    def infer(
        self,
        subject_id: EntityId,
        evidence: tuple[EvidenceRecord, ...],
        inferred_at: datetime,
    ) -> KnowledgeFact | None:
        """Infer a Knowledge fact from Evidence when applicable."""
        ...


def latest_evidence_by_kind(
    evidence: Iterable[EvidenceRecord],
) -> dict[EvidenceKind, EvidenceRecord]:
    """Return the newest Evidence record for each kind."""
    latest: dict[EvidenceKind, EvidenceRecord] = {}
    for record in evidence:
        existing = latest.get(record.kind)
        if existing is None or record.provenance.observed_at > existing.provenance.observed_at:
            latest[record.kind] = record
    return latest


@dataclass(frozen=True, slots=True)
class CoreMetadataCompleteRule:
    """Infer whether title, artist, and album metadata are all present."""

    rule_id: str = "metadata.core-complete"
    rule_version: str = "1"

    def infer(
        self,
        subject_id: EntityId,
        evidence: tuple[EvidenceRecord, ...],
        inferred_at: datetime,
    ) -> KnowledgeFact | None:
        latest = latest_evidence_by_kind(evidence)
        required = (
            EvidenceKind.TITLE,
            EvidenceKind.ARTIST,
            EvidenceKind.ALBUM,
        )
        records = tuple(latest[kind] for kind in required if kind in latest)
        if not records:
            return None

        complete = len(records) == len(required) and all(
            isinstance(record.value, str) and bool(record.value.strip()) for record in records
        )
        return KnowledgeFact(
            subject_id=subject_id,
            kind=KnowledgeKind.CORE_METADATA_COMPLETE,
            value=complete,
            confidence=Confidence(1.0),
            evidence_ids=tuple(record.id for record in records),
            rule_id=self.rule_id,
            rule_version=self.rule_version,
            inferred_at=inferred_at,
        )


@dataclass(frozen=True, slots=True)
class HighResolutionFormatRule:
    """Infer whether format characteristics meet Orion's technical hi-res rule.

    The rule is intentionally technical rather than a statement about audible
    quality: sample rate >= 88.2 kHz OR bit depth >= 24 bits.
    """

    rule_id: str = "audio.high-resolution-format"
    rule_version: str = "1"

    def infer(
        self,
        subject_id: EntityId,
        evidence: tuple[EvidenceRecord, ...],
        inferred_at: datetime,
    ) -> KnowledgeFact | None:
        latest = latest_evidence_by_kind(evidence)
        sample_rate = latest.get(EvidenceKind.SAMPLE_RATE)
        bit_depth = latest.get(EvidenceKind.BITS_PER_SAMPLE)
        records = tuple(record for record in (sample_rate, bit_depth) if record is not None)
        if not records:
            return None

        sample_rate_value = (
            int(sample_rate.value)
            if sample_rate is not None and isinstance(sample_rate.value, int)
            else None
        )
        bit_depth_value = (
            int(bit_depth.value)
            if bit_depth is not None and isinstance(bit_depth.value, int)
            else None
        )
        is_high_resolution = (sample_rate_value is not None and sample_rate_value >= 88_200) or (
            bit_depth_value is not None and bit_depth_value >= 24
        )

        return KnowledgeFact(
            subject_id=subject_id,
            kind=KnowledgeKind.HIGH_RESOLUTION_FORMAT,
            value=is_high_resolution,
            confidence=Confidence(1.0),
            evidence_ids=tuple(record.id for record in records),
            rule_id=self.rule_id,
            rule_version=self.rule_version,
            inferred_at=inferred_at,
        )


DEFAULT_KNOWLEDGE_RULES: tuple[KnowledgeRule, ...] = (
    CoreMetadataCompleteRule(),
    HighResolutionFormatRule(),
)
