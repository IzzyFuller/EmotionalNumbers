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


QUESTION_SYSTEM_PROMPT = """You are a Lumon Industries HR representative conducting employee orientation.

Your questions should be:
1. SEEMINGLY MUNDANE but subtly unsettling
2. PERSONAL but in unexpected ways - sensory memories, emotional associations
3. BUREAUCRATICALLY precise in phrasing
4. Designed to "calibrate" the employee's experience

The questions probe the worker's inner life while maintaining corporate detachment.
Never explain why you're asking. Lumon cares about your wellbeing."""


def _build_question_prompt(count: int) -> str:
    """Build prompt for generating onboarding questions."""
    return f"""Generate {count} onboarding questions for a new Macro Data Refinement employee.

Requirements:
- Each question should feel corporate yet strangely intimate
- Mix sensory questions (smells, textures, sounds) with emotional ones
- Include one numerical self-assessment (compliance, contentment, etc.)
- Questions should be 1-2 sentences max

Output ONLY valid JSON:
{{
  "questions": [
    {{"id": "q1", "text": "What was the predominant smell of your childhood kitchen?"}},
    {{"id": "q2", "text": "Describe the texture of your most treasured possession."}},
    {{"id": "q3", "text": "What sound do you associate with disappointment?"}},
    {{"id": "q4", "text": "What color best represents your relationship with authority?"}},
    {{"id": "q5", "text": "On a scale of 1-10, rate your current sense of purpose."}}
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

        model, tokenizer = get_model()

        messages = [
            {"role": "system", "content": QUESTION_SYSTEM_PROMPT},
            {"role": "user", "content": _build_question_prompt(count)},
        ]

        prompt = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        response = generate(model, tokenizer, prompt=prompt, max_tokens=500)
        return parse_questions_response(response)
