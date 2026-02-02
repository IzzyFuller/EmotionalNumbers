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


class BucketEmotion(BaseModel):
    """Emotional qualities for a bucket."""

    id: str
    emotion: str
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


class BucketsResponse(BaseModel):
    """LLM response for bucket emotions."""

    buckets: list[BucketEmotion]


# ============================================================================
# Prompt Building
# ============================================================================


def _build_emotions_prompt(answers: list[dict]) -> str:
    """Build prompt for 5 bucket emotions based on answers."""
    answers_formatted = "\n".join(
        f"- {a['questionId']}: {a['answer']}" for a in answers
    )

    return f"""Worker responses:
{answers_formatted}

Create 5 emotional qualities for data buckets based on their answers.

Output JSON:
{{
  "buckets": [
    {{"id": "01", "emotion": "WORD", "intensity": 0.5, "frequency": 1.0}},
    {{"id": "02", "emotion": "WORD", "intensity": 0.5, "frequency": 1.0}},
    {{"id": "03", "emotion": "WORD", "intensity": 0.5, "frequency": 1.0}},
    {{"id": "04", "emotion": "WORD", "intensity": 0.5, "frequency": 1.0}},
    {{"id": "05", "emotion": "WORD", "intensity": 0.5, "frequency": 1.0}}
  ]
}}

Replace WORD with feelings from their answers. Vary intensity (0.2-1.0) and frequency (0.5-2.0)."""


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
        regions = generate_regions(rows=rows, cols=cols, num_regions=20, seed=seed)

        # Step 2: LLM assigns emotional qualities
        model, tokenizer = get_model()
        sampler = make_sampler(temp=0.7)

        emotions_prompt = tokenizer.apply_chat_template(
            [{"role": "user", "content": _build_emotions_prompt(answers)}],
            tokenize=False,
            add_generation_prompt=True,
        )
        emotions_raw = generate(
            model, tokenizer, prompt=emotions_prompt, max_tokens=300, sampler=sampler
        )
        bucket_emotions = self._parse_bucket_emotions(emotions_raw)

        return self._build_ruleset(regions, bucket_emotions)

    def _parse_bucket_emotions(self, raw: str) -> list[BucketEmotion]:
        """Parse LLM bucket emotions response."""
        json_match = re.search(r"\{[\s\S]*\}", raw)
        if not json_match:
            raise RuleValidationError("No JSON found in emotions response")

        data = json.loads(json_match.group())
        return BucketsResponse.model_validate(data).buckets

    def _build_ruleset(self, regions, bucket_emotions: list[BucketEmotion]) -> RuleSet:
        """Combine algorithmic regions with LLM bucket emotions."""
        # Map bucket id to emotion
        emotion_map = {e.id: e for e in bucket_emotions}
        buckets = ["01", "02", "03", "04", "05"]

        domain_regions = []
        behaviors_by_bucket: dict[str, RegionBehavior] = {}

        # Cycle regions through 5 buckets
        for i, region in enumerate(regions):
            bucket = buckets[i % 5]
            emotion = emotion_map.get(bucket)

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
