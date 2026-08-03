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
    KnowledgeRepository,
    LibraryRepository,
    ReconciliationRepository,
    RecordingRepository,
    RecoveryApprovalRepository,
    RecoveryRepository,
    ReviewRepository,
    TrackAppearanceRepository,
)


class UnitOfWork(Protocol):
    libraries: LibraryRepository
    artists: ArtistRepository
    albums: AlbumRepository
    editions: EditionRepository
    discs: DiscRepository
    recordings: RecordingRepository
    track_appearances: TrackAppearanceRepository
    audio_files: AudioFileRepository
    evidence: EvidenceRepository
    knowledge: KnowledgeRepository
    decisions: DecisionRepository
    reviews: ReviewRepository
    authorizations: AuthorizationRepository
    action_plans: ActionPlanRepository
    executions: ExecutionRepository
    reconciliations: ReconciliationRepository
    recovery_approvals: RecoveryApprovalRepository
    recoveries: RecoveryRepository

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
