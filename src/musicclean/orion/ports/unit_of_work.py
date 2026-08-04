"""Unit-of-work ports for atomic application use cases."""

from __future__ import annotations

from types import TracebackType
from typing import Protocol, Self

from musicclean.orion.ports.repositories import (
    ActionPlanRepository,
    AlbumRepository,
    ArtistRepository,
    AudioFileRepository,
    AuthorizationRepository,
    DecisionRepository,
    DiscRepository,
    EditionRepository,
    EvidenceRepository,
    ExecutionRepository,
    IdempotencyRepository,
    KnowledgeRepository,
    LeaseRepository,
    LibraryRepository,
    ReconciliationRepository,
    RecordingRepository,
    RecoveryApprovalRepository,
    RecoveryRepository,
    ReviewRepository,
    TrackAppearanceRepository,
)


class UnitOfWork(Protocol):
    @property
    def libraries(self) -> LibraryRepository: ...

    @property
    def artists(self) -> ArtistRepository: ...

    @property
    def albums(self) -> AlbumRepository: ...

    @property
    def editions(self) -> EditionRepository: ...

    @property
    def discs(self) -> DiscRepository: ...

    @property
    def recordings(self) -> RecordingRepository: ...

    @property
    def track_appearances(self) -> TrackAppearanceRepository: ...

    @property
    def audio_files(self) -> AudioFileRepository: ...

    @property
    def evidence(self) -> EvidenceRepository: ...

    @property
    def knowledge(self) -> KnowledgeRepository: ...

    @property
    def decisions(self) -> DecisionRepository: ...

    @property
    def reviews(self) -> ReviewRepository: ...

    @property
    def authorizations(self) -> AuthorizationRepository: ...

    @property
    def action_plans(self) -> ActionPlanRepository: ...

    @property
    def executions(self) -> ExecutionRepository: ...

    @property
    def reconciliations(self) -> ReconciliationRepository: ...

    @property
    def recovery_approvals(self) -> RecoveryApprovalRepository: ...

    @property
    def recoveries(self) -> RecoveryRepository: ...

    @property
    def idempotency(self) -> IdempotencyRepository: ...

    @property
    def leases(self) -> LeaseRepository: ...

    def __enter__(self) -> Self: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...


class UnitOfWorkFactory(Protocol):
    def __call__(self) -> UnitOfWork: ...
