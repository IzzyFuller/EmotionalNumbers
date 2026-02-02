"""LLM-based questions adapter using MLX."""

from __future__ import annotations

import json
import re

from pydantic import BaseModel

from emotional_numbers_mk_ii.adapters.llm.model_loader import get_model


class LLMQuestion(BaseModel):
    """A question from LLM output."""

    id: str
    text: str


class LLMQuestionsResponse(BaseModel):
    """LLM response for question generation."""

    questions: list[LLMQuestion]


QUESTION_SYSTEM_PROMPT = """You generate short, simple questions. Each question is one sentence. No descriptions or explanations."""


def _build_question_prompt(count: int) -> str:
    """Build prompt for generating onboarding questions."""
    return f"""Generate {count} short questions for a quirky corporate onboarding survey.

Each question should:
- Be one simple sentence
- Ask about personal preferences, memories, sensations, or associations
- Feel slightly unusual or unexpected, like a personality test from a strange company
- Vary in format: some ask for descriptions, some for choices, some for ratings, some for single words

Output ONLY this JSON:
{{
  "questions": [
    {{"id": "q1", "text": "Your question here?"}},
    {{"id": "q2", "text": "Your question here?"}},
    {{"id": "q3", "text": "Your question here?"}},
    {{"id": "q4", "text": "Your question here?"}},
    {{"id": "q5", "text": "Your question here?"}}
  ]
}}"""


class QuestionParseError(Exception):
    """Error parsing LLM question response."""


def parse_questions_response(raw: str) -> list[dict]:
    """Parse LLM JSON response into question list."""
    json_match = re.search(r"\{[\s\S]*\}", raw)
    if not json_match:
        raise QuestionParseError("No JSON found in question response")

    data = json.loads(json_match.group())
    response = LLMQuestionsResponse.model_validate(data)

    return [{"id": q.id, "text": q.text} for q in response.questions]


class LLMQuestionsAdapter:
    """LLM-based question generator using MLX.

    Implements QuestionsRepository protocol.
    """

    def get_questions(self, count: int = 5) -> list[dict]:
        """Generate onboarding questions using MLX LLM.

        Args:
            count: Number of questions to generate.

        Returns:
            List of question dicts with 'id' and 'text' keys.
        """
        from mlx_lm import generate
        from mlx_lm.sample_utils import make_sampler

        model, tokenizer = get_model()

        messages = [
            {"role": "system", "content": QUESTION_SYSTEM_PROMPT},
            {"role": "user", "content": _build_question_prompt(count)},
        ]

        prompt = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        sampler = make_sampler(temp=0.7)
        response = generate(
            model, tokenizer, prompt=prompt, max_tokens=500, sampler=sampler
        )
        return parse_questions_response(response)
