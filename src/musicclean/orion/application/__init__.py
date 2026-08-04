"""Orion application use cases."""

from musicclean.orion.application.collect_metadata_evidence import (
    CollectMetadataEvidence,
    collect_metadata_evidence,
)
from musicclean.orion.application.coordination import (
    CoordinatedExecution,
    CoordinatedRecovery,
    apply_recovery_coordinated,
    execute_quarantine_coordinated,
    restore_quarantine_coordinated,
)
from musicclean.orion.application.create_library import CreateLibrary, create_library
from musicclean.orion.application.decision_rules import (
    DecisionRule,
    HighResolutionReviewRule,
    MetadataRepairRecommendationRule,
    latest_knowledge_by_kind,
)
from musicclean.orion.application.errors import (
    ApplicationError,
    ConflictError,
    NotFoundError,
)
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
from musicclean.orion.application.operational_hardening import (
    AcquirePlanLease,
    BeginIdempotentOperation,
    StartupRecoverySweep,
    acquire_plan_lease,
    begin_idempotent_operation,
    complete_idempotent_operation,
    release_plan_lease,
    startup_recovery_sweep,
)
from musicclean.orion.application.read_metadata import ReadMetadata, read_metadata
from musicclean.orion.application.reconcile_execution import (
    ReconcileActionPlan,
    classify_reconciliation,
    reconcile_action_plan,
)
from musicclean.orion.application.recovery_actions import (
    ApplyRecovery,
    ApproveRecovery,
    apply_recovery,
    approve_recovery,
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
from musicclean.orion.application.service import (
    OrionService,
    QuarantineRequest,
    ReconcileRequest,
    RestoreRequest,
)
from musicclean.orion.application.service_models import (
    ServiceExecutionResult,
    ServiceHealth,
    ServiceReconciliationResult,
)
from musicclean.orion.application.synchronize_filesystem import (
    SynchronizationSummary,
    SynchronizeFilesystem,
    synchronize_filesystem,
)

__all__ = [
    "AcquirePlanLease",
    "ApplicationError",
    "ApplyRecovery",
    "ApproveRecovery",
    "AuthorizeDecision",
    "BeginIdempotentOperation",
    "CollectMetadataEvidence",
    "ConflictError",
    "CoordinatedExecution",
    "CoordinatedRecovery",
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
    "OrionService",
    "PlanQuarantine",
    "PlannedQuarantine",
    "QuarantineRequest",
    "ReadMetadata",
    "ReconcileActionPlan",
    "ReconcileRequest",
    "RegisterAudioFile",
    "RestoreQuarantine",
    "RestoreRequest",
    "ReviewDecision",
    "ServiceExecutionResult",
    "ServiceHealth",
    "ServiceReconciliationResult",
    "StartupRecoverySweep",
    "SyncChange",
    "SyncDecision",
    "SynchronizationSummary",
    "SynchronizeFilesystem",
    "acquire_plan_lease",
    "apply_recovery",
    "apply_recovery_coordinated",
    "approve_recovery",
    "authorize_decision",
    "begin_idempotent_operation",
    "classify_observation",
    "classify_reconciliation",
    "collect_metadata_evidence",
    "complete_idempotent_operation",
    "create_library",
    "execute_quarantine",
    "execute_quarantine_coordinated",
    "generate_decisions",
    "infer_knowledge",
    "latest_evidence_by_kind",
    "latest_knowledge_by_kind",
    "list_album_editions",
    "plan_quarantine",
    "read_metadata",
    "reconcile_action_plan",
    "register_audio_file",
    "release_plan_lease",
    "restore_quarantine",
    "restore_quarantine_coordinated",
    "review_decision",
    "startup_recovery_sweep",
    "synchronize_filesystem",
]
