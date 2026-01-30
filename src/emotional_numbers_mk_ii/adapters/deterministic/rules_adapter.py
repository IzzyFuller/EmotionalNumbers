"""Deterministic rules adapter - wraps domain generate_rule_set."""

from __future__ import annotations

from emotional_numbers_mk_ii.domain.game import (
    RuleSet,
    answers_to_seed,
    generate_rule_set,
)


class DeterministicRulesAdapter:
    """Rules adapter using deterministic generation.

    Implements RulesRepository protocol.
    Wraps the domain's generate_rule_set() function.
    """

    def __init__(self, seed: int | None = None):
        """Initialize with optional fixed seed.

        Args:
            seed: Fixed seed to use instead of deriving from answers.
                  If None, seed is derived from answers.
        """
        self._fixed_seed = seed

    def generate_rules(self, answers: list[dict], rows: int, cols: int) -> RuleSet:
        """Generate rules deterministically from answers.

        Args:
            answers: List of answer dicts (used to derive seed if no fixed seed).
            rows: Grid height.
            cols: Grid width.

        Returns:
            RuleSet with regions and behaviors.
        """
        seed = (
            self._fixed_seed
            if self._fixed_seed is not None
            else answers_to_seed(answers)
        )
        return generate_rule_set(seed, rows=rows, cols=cols)
