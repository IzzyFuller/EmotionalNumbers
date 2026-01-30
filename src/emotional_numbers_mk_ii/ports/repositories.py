"""Repository protocols defining what the domain needs."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from emotional_numbers_mk_ii.domain.game import RuleSet


@runtime_checkable
class QuestionsRepository(Protocol):
    """Port for retrieving onboarding questions."""

    def get_questions(self, count: int = 5) -> list[dict]:
        """Return onboarding questions.

        Args:
            count: Number of questions to return.

        Returns:
            List of question dicts with 'id' and 'text' keys.
        """
        ...


@runtime_checkable
class RulesRepository(Protocol):
    """Port for generating game rules."""

    def generate_rules(self, answers: list[dict], rows: int, cols: int) -> RuleSet:
        """Generate rules from onboarding answers.

        Args:
            answers: List of answer dicts with 'questionId' and 'answer' keys.
            rows: Grid height.
            cols: Grid width.

        Returns:
            RuleSet defining regions and behaviors for the game.
        """
        ...
