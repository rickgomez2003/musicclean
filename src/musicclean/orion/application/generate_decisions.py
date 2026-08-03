"""Generate and persist explainable Decisions from Knowledge."""

from __future__ import annotations

from dataclasses import dataclass

from musicclean.orion.application.decision_rules import (
    DEFAULT_DECISION_RULES,
    DecisionRule,
)
from musicclean.orion.application.errors import NotFoundError
from musicclean.orion.domain import Decision
from musicclean.orion.ports import UnitOfWorkFactory
from musicclean.orion.shared import Clock, EntityId


@dataclass(frozen=True, slots=True)
class GenerateDecisions:
    """Command for generating recommendations for one AudioFile."""

    audio_file_id: EntityId


def generate_decisions(
    command: GenerateDecisions,
    clock: Clock,
    uow_factory: UnitOfWorkFactory,
    rules: tuple[DecisionRule, ...] = DEFAULT_DECISION_RULES,
) -> tuple[Decision, ...]:
    """Run decision rules against persisted Knowledge and append recommendations."""
    with uow_factory() as uow:
        if uow.audio_files.get(command.audio_file_id) is None:
            raise NotFoundError(f"audio file not found: {command.audio_file_id}")

        knowledge = uow.knowledge.list_for_subject(command.audio_file_id)
        decided_at = clock.now()
        decisions = tuple(
            decision
            for rule in rules
            if (
                decision := rule.decide(
                    command.audio_file_id,
                    knowledge,
                    decided_at,
                )
            )
            is not None
        )
        uow.decisions.save_many(decisions)
        uow.commit()
        return decisions
