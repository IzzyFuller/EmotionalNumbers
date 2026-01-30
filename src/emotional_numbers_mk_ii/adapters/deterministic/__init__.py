"""Deterministic adapters - no external dependencies."""

from emotional_numbers_mk_ii.adapters.deterministic.questions_adapter import (
    DeterministicQuestionsAdapter,
)
from emotional_numbers_mk_ii.adapters.deterministic.rules_adapter import (
    DeterministicRulesAdapter,
)

__all__ = ["DeterministicQuestionsAdapter", "DeterministicRulesAdapter"]
