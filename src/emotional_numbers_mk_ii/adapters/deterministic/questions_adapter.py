"""Deterministic questions adapter - selects from static question bank."""

from __future__ import annotations

import random

from emotional_numbers_mk_ii.adapters.deterministic.question_bank import QUESTION_BANK


class DeterministicQuestionsAdapter:
    """Questions adapter using static question bank.

    Implements QuestionsRepository protocol.
    """

    def __init__(self, seed: int | None = None):
        """Initialize with optional seed for reproducible selection.

        Args:
            seed: Random seed for question selection. None uses random selection.
        """
        self._seed = seed

    def get_questions(self, count: int = 5) -> list[dict]:
        """Return questions from the static bank.

        Args:
            count: Number of questions to return.

        Returns:
            List of question dicts with 'id' and 'text' keys.
        """
        if count >= len(QUESTION_BANK):
            return list(QUESTION_BANK)

        rng = random.Random(self._seed)
        selected = rng.sample(QUESTION_BANK, count)
        return [{"id": q["id"], "text": q["text"]} for q in selected]
