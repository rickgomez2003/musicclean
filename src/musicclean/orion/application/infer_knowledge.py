"""Infer and persist Knowledge from Evidence."""

from __future__ import annotations

from dataclasses import dataclass

from musicclean.orion.application.errors import NotFoundError
from musicclean.orion.application.knowledge_rules import (
    DEFAULT_KNOWLEDGE_RULES,
    KnowledgeRule,
)
from musicclean.orion.domain import KnowledgeFact
from musicclean.orion.ports import UnitOfWorkFactory
from musicclean.orion.shared import Clock, EntityId


@dataclass(frozen=True, slots=True)
class InferKnowledge:
    """Command for running deterministic rules for one AudioFile."""

    audio_file_id: EntityId


def infer_knowledge(
    command: InferKnowledge,
    clock: Clock,
    uow_factory: UnitOfWorkFactory,
    rules: tuple[KnowledgeRule, ...] = DEFAULT_KNOWLEDGE_RULES,
) -> tuple[KnowledgeFact, ...]:
    """Run rules against persisted Evidence and append resulting Knowledge."""
    with uow_factory() as uow:
        if uow.audio_files.get(command.audio_file_id) is None:
            raise NotFoundError(f"audio file not found: {command.audio_file_id}")

        evidence = uow.evidence.list_for_subject(command.audio_file_id)
        inferred_at = clock.now()
        facts = tuple(
            fact
            for rule in rules
            if (
                fact := rule.infer(
                    command.audio_file_id,
                    evidence,
                    inferred_at,
                )
            )
            is not None
        )
        uow.knowledge.save_many(facts)
        uow.commit()
        return facts
