"""Orion application use cases."""

from musicclean.orion.application.collect_metadata_evidence import (
    CollectMetadataEvidence,
    collect_metadata_evidence,
)
from musicclean.orion.application.create_library import CreateLibrary, create_library
from musicclean.orion.application.decision_rules import (
    DecisionRule,
    HighResolutionReviewRule,
    MetadataRepairRecommendationRule,
    latest_knowledge_by_kind,
)
from musicclean.orion.application.errors import ApplicationError, ConflictError, NotFoundError
from musicclean.orion.application.filesystem_sync import (
    FileObservation,
    SyncChange,
    SyncDecision,
    classify_observation,
)
from musicclean.orion.application.generate_decisions import (
    GenerateDecisions,
    generate_decisions,
)
from musicclean.orion.application.infer_knowledge import InferKnowledge, infer_knowledge
from musicclean.orion.application.knowledge_rules import (
    CoreMetadataCompleteRule,
    HighResolutionFormatRule,
    KnowledgeRule,
    latest_evidence_by_kind,
)
from musicclean.orion.application.list_album_editions import (
    ListAlbumEditions,
    list_album_editions,
)
from musicclean.orion.application.read_metadata import ReadMetadata, read_metadata
from musicclean.orion.application.reconcile_execution import (
    ReconcileActionPlan,
    classify_reconciliation,
    reconcile_action_plan,
)
from musicclean.orion.application.register_audio_file import (
    RegisterAudioFile,
    register_audio_file,
)
from musicclean.orion.application.review_execution import (
    AuthorizeDecision,
    PlannedQuarantine,
    PlanQuarantine,
    ReviewDecision,
    authorize_decision,
    plan_quarantine,
    review_decision,
)
from musicclean.orion.application.safe_executor import (
    ExecuteQuarantine,
    RestoreQuarantine,
    execute_quarantine,
    restore_quarantine,
)
from musicclean.orion.application.synchronize_filesystem import (
    SynchronizationSummary,
    SynchronizeFilesystem,
    synchronize_filesystem,
)

__all__ = [
    "ApplicationError",
    "AuthorizeDecision",
    "CollectMetadataEvidence",
    "ConflictError",
    "CoreMetadataCompleteRule",
    "CreateLibrary",
    "DecisionRule",
    "ExecuteQuarantine",
    "FileObservation",
    "GenerateDecisions",
    "HighResolutionFormatRule",
    "HighResolutionReviewRule",
    "InferKnowledge",
    "KnowledgeRule",
    "ListAlbumEditions",
    "MetadataRepairRecommendationRule",
    "NotFoundError",
    "PlanQuarantine",
    "PlannedQuarantine",
    "ReadMetadata",
    "ReconcileActionPlan",
    "RegisterAudioFile",
    "RestoreQuarantine",
    "ReviewDecision",
    "SyncChange",
    "SyncDecision",
    "SynchronizationSummary",
    "SynchronizeFilesystem",
    "authorize_decision",
    "classify_observation",
    "classify_reconciliation",
    "collect_metadata_evidence",
    "create_library",
    "execute_quarantine",
    "generate_decisions",
    "infer_knowledge",
    "latest_evidence_by_kind",
    "latest_knowledge_by_kind",
    "list_album_editions",
    "plan_quarantine",
    "read_metadata",
    "reconcile_action_plan",
    "register_audio_file",
    "restore_quarantine",
    "review_decision",
    "synchronize_filesystem",
]
