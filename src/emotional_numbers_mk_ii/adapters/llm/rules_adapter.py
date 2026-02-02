"""Hybrid rules adapter: algorithmic regions + LLM emotional assignment."""

from __future__ import annotations

import json
import re

from pydantic import BaseModel, field_validator

from emotional_numbers_mk_ii.adapters.llm.model_loader import get_model
from emotional_numbers_mk_ii.adapters.llm.region_generator import generate_regions
from emotional_numbers_mk_ii.domain.game import Region, RegionBehavior, RuleSet


# ============================================================================
# Pydantic Models
# ============================================================================


class EmotionAssignment(BaseModel):
    """Emotional assignment for a region."""

    region_id: int
    bucket: str
    rule: str
    intensity: float
    frequency: float

    @field_validator("intensity")
    @classmethod
    def clamp_intensity(cls, v: float) -> float:
        return max(0.2, min(1.0, v))

    @field_validator("frequency")
    @classmethod
    def clamp_frequency(cls, v: float) -> float:
        return max(0.5, min(2.0, v))


class EmotionsResponse(BaseModel):
    """LLM response for emotional assignments."""

    assignments: list[EmotionAssignment]


# ============================================================================
# Prompt Building
# ============================================================================


def _build_emotions_prompt(answers: list[dict], num_regions: int) -> str:
    """Build prompt for emotional assignment."""
    answers_formatted = "\n".join(
        f"- {a['questionId']}: {a['answer']}" for a in answers
    )

    return f"""Worker responses:
{answers_formatted}

Assign emotional qualities to {num_regions} regions based on the worker's answers above.
Create unique rules that reflect their personality.

Output JSON:
{{
  "assignments": [
    {{"region_id": 1, "bucket": "01", "rule": "<QUALITY_FROM_ANSWERS>", "intensity": <0.2-1.0>, "frequency": <0.5-2.0>}},
    {{"region_id": 2, "bucket": "02", "rule": "<QUALITY_FROM_ANSWERS>", "intensity": <0.2-1.0>, "frequency": <0.5-2.0>}},
    {{"region_id": 3, "bucket": "03", "rule": "<QUALITY_FROM_ANSWERS>", "intensity": <0.2-1.0>, "frequency": <0.5-2.0>}},
    {{"region_id": 4, "bucket": "04", "rule": "<QUALITY_FROM_ANSWERS>", "intensity": <0.2-1.0>, "frequency": <0.5-2.0>}},
    {{"region_id": 5, "bucket": "05", "rule": "<QUALITY_FROM_ANSWERS>", "intensity": <0.2-1.0>, "frequency": <0.5-2.0>}}
  ]
}}"""


# ============================================================================
# Errors
# ============================================================================


class RuleValidationError(Exception):
    """Error during rule validation."""


# ============================================================================
# Adapter
# ============================================================================


class LLMRulesAdapter:
    """Hybrid rule generator: algorithmic regions + LLM emotional assignment.

    Implements RulesRepository protocol.
    """

    def generate_rules(self, answers: list[dict], rows: int, cols: int) -> RuleSet:
        """Generate rules: algorithmic regions, LLM emotions.

        Args:
            answers: List of answer dicts with 'questionId' and 'answer' keys.
            rows: Grid height.
            cols: Grid width.

        Returns:
            RuleSet with regions and behaviors.
        """
        from mlx_lm import generate
        from mlx_lm.sample_utils import make_sampler

        # Step 1: Generate regions algorithmically (guaranteed valid)
        seed = _answers_to_seed(answers)
        regions = generate_regions(rows=rows, cols=cols, num_regions=5, seed=seed)

        # Step 2: LLM assigns emotional qualities
        model, tokenizer = get_model()
        sampler = make_sampler(temp=0.7)

        emotions_prompt = tokenizer.apply_chat_template(
            [
                {
                    "role": "user",
                    "content": _build_emotions_prompt(answers, len(regions)),
                }
            ],
            tokenize=False,
            add_generation_prompt=True,
        )
        emotions_raw = generate(
            model, tokenizer, prompt=emotions_prompt, max_tokens=600, sampler=sampler
        )
        emotions = self._parse_emotions(emotions_raw)

        return self._build_ruleset(regions, emotions)

    def _parse_emotions(self, raw: str) -> list[EmotionAssignment]:
        """Parse LLM emotions response."""
        json_match = re.search(r"\{[\s\S]*\}", raw)
        if not json_match:
            raise RuleValidationError("No JSON found in emotions response")

        data = json.loads(json_match.group())
        return EmotionsResponse.model_validate(data).assignments

    def _build_ruleset(self, regions, emotions: list[EmotionAssignment]) -> RuleSet:
        """Combine algorithmic regions with LLM emotions."""
        emotion_map = {e.region_id: e for e in emotions}

        domain_regions = []
        behaviors_by_bucket: dict[str, RegionBehavior] = {}

        for region in regions:
            emotion = emotion_map.get(region.id)
            bucket = emotion.bucket if emotion else f"0{region.id}"

            domain_regions.append(
                Region(bucket=bucket, positions=list(region.positions))
            )

            if bucket not in behaviors_by_bucket:
                behaviors_by_bucket[bucket] = RegionBehavior(
                    bucket=bucket,
                    jiggle_intensity=emotion.intensity if emotion else 0.5,
                    jiggle_frequency=emotion.frequency if emotion else 1.0,
                    sound_id=f"tone_{bucket}",
                )

        return RuleSet(
            regions=domain_regions, behaviors=list(behaviors_by_bucket.values())
        )


def _answers_to_seed(answers: list[dict]) -> int:
    """Convert answers to a deterministic seed."""
    combined = "|".join(f"{a['questionId']}:{a['answer']}" for a in answers)
    hash_val = 0
    for char in combined:
        hash_val = ((hash_val << 5) - hash_val + ord(char)) & 0xFFFFFFFF
    return hash_val
