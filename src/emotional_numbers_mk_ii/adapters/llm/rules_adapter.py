"""LLM-based rules adapter using MLX."""

from __future__ import annotations

import json
import re

from pydantic import BaseModel, field_validator

from emotional_numbers_mk_ii.adapters.llm.model_loader import get_model
from emotional_numbers_mk_ii.adapters.llm.prompts import SYSTEM_PROMPT
from emotional_numbers_mk_ii.domain.game import Region, RegionBehavior, RuleSet


# ============================================================================
# Pydantic Models for LLM Response
# ============================================================================


class LLMRegion(BaseModel):
    """A region from LLM output."""

    bucket: str
    positions: list[tuple[int, int]]

    @field_validator("positions", mode="before")
    @classmethod
    def convert_positions(cls, v: list) -> list[tuple[int, int]]:
        """Convert [[x, y], ...] to [(x, y), ...]."""
        return [tuple(pos) for pos in v]


class LLMBehavior(BaseModel):
    """Behavior parameters from LLM output."""

    bucket: str
    jiggle_intensity: float
    jiggle_frequency: float
    sound_id: str

    @field_validator("jiggle_intensity")
    @classmethod
    def validate_intensity(cls, v: float) -> float:
        """Clamp intensity to valid range, avoiding reserved default."""
        v = max(0.2, min(1.0, v))
        # Avoid reserved default value
        if abs(v - 0.15) < 0.01:
            v = 0.2
        return v

    @field_validator("jiggle_frequency")
    @classmethod
    def validate_frequency(cls, v: float) -> float:
        """Clamp frequency to valid range, avoiding reserved default."""
        v = max(0.5, min(2.0, v))
        # Avoid reserved default value
        if abs(v - 0.8) < 0.01:
            v = 0.75
        return v

    @field_validator("sound_id")
    @classmethod
    def validate_sound_id(cls, v: str) -> str:
        """Ensure sound_id is not the reserved default."""
        if v == "tone_00":
            return "tone_01"
        return v


class LLMRuleResponse(BaseModel):
    """Complete LLM response for rule generation."""

    hidden_rules: dict[str, str]
    regions: list[LLMRegion]
    behaviors: list[LLMBehavior]


# ============================================================================
# Prompt Building
# ============================================================================


def _build_user_prompt(answers: list[dict], rows: int, cols: int) -> str:
    """Build the user prompt content."""
    answers_formatted = "\n".join(
        f"- Question {a['questionId']}: {a['answer']}" for a in answers
    )

    return f"""Worker onboarding responses:
{answers_formatted}

Create 5 classification regions for a {cols}x{rows} grid (x: 0-{cols - 1}, y: 0-{rows - 1}).

CRITICAL - NO OVERLAPPING CELLS:
- Each cell coordinate can only appear in ONE region
- Before adding a position, verify it is not already used by another region
- If you reuse a coordinate, the puzzle will be invalid

Each region:
- 2 to 20 contiguous cells (vary the sizes)
- All 5 buckets (01-05) must have at least one region

Behavior constraints:
- jiggle_intensity: between 0.2 and 1.0
- jiggle_frequency: between 0.5 and 2.0
- sound_id: assign one of these tones to each bucket based on its emotional quality:
  * tone_01: low, grounded, stable
  * tone_02: warm, hopeful
  * tone_03: tense, unsettled
  * tone_04: bright, alert
  * tone_05: high, ethereal

Based on the worker's answers, create hidden rules connecting each bucket to an emotional quality. Then assign the tone that best fits each bucket's emotional character.

Output ONLY valid JSON:
{{
  "hidden_rules": {{
    "01": "YOUR RULE",
    "02": "YOUR RULE",
    "03": "YOUR RULE",
    "04": "YOUR RULE",
    "05": "YOUR RULE"
  }},
  "regions": [
    {{"bucket": "01", "positions": [[x, y], [x, y], ...]}}
  ],
  "behaviors": [
    {{"bucket": "01", "jiggle_intensity": VALUE, "jiggle_frequency": VALUE, "sound_id": "tone_XX"}}
  ]
}}"""


# ============================================================================
# Response Parsing and Validation
# ============================================================================


class RuleValidationError(Exception):
    """Error during rule validation."""


def validate_regions(regions: list[LLMRegion], rows: int, cols: int) -> None:
    """Validate regions don't overlap and are in bounds."""
    used_positions: set[tuple[int, int]] = set()
    buckets = {"01", "02", "03", "04", "05"}

    for region in regions:
        # Validate bucket
        if region.bucket not in buckets:
            raise RuleValidationError(f"Invalid bucket: {region.bucket}")

        # Validate region size (at least 2 cells, reasonable max)
        if not (2 <= len(region.positions) <= 20):
            raise RuleValidationError(
                f"Region size {len(region.positions)} out of range [2, 20]"
            )

        for x, y in region.positions:
            # Check bounds
            if not (0 <= x < cols and 0 <= y < rows):
                raise RuleValidationError(f"Position ({x}, {y}) out of bounds")

            # Check overlap
            if (x, y) in used_positions:
                raise RuleValidationError(
                    f"Position ({x}, {y}) overlaps with another region"
                )

            used_positions.add((x, y))


def convert_to_ruleset(response: LLMRuleResponse) -> RuleSet:
    """Convert LLM response to domain RuleSet."""
    regions = [
        Region(bucket=r.bucket, positions=list(r.positions)) for r in response.regions
    ]

    behaviors = [
        RegionBehavior(
            bucket=b.bucket,
            jiggle_intensity=b.jiggle_intensity,
            jiggle_frequency=b.jiggle_frequency,
            sound_id=b.sound_id,
        )
        for b in response.behaviors
    ]

    return RuleSet(regions=regions, behaviors=behaviors)


def parse_llm_response(raw: str, rows: int, cols: int) -> RuleSet:
    """Parse LLM JSON response into RuleSet."""
    # Extract JSON from response (may have preamble)
    json_match = re.search(r"\{[\s\S]*\}", raw)
    if not json_match:
        raise RuleValidationError("No JSON found in response")

    data = json.loads(json_match.group())
    response = LLMRuleResponse.model_validate(data)

    # Validate regions
    validate_regions(response.regions, rows, cols)

    return convert_to_ruleset(response)


# ============================================================================
# LLM Rules Adapter
# ============================================================================


class LLMRulesAdapter:
    """LLM-based rule generator using MLX.

    Implements RulesRepository protocol.
    """

    def generate_rules(self, answers: list[dict], rows: int, cols: int) -> RuleSet:
        """Generate rules using MLX LLM.

        Args:
            answers: List of answer dicts with 'questionId' and 'answer' keys.
            rows: Grid height.
            cols: Grid width.

        Returns:
            RuleSet with regions and behaviors.
        """
        from mlx_lm import generate
        from mlx_lm.sample_utils import make_sampler

        model, tokenizer = get_model()

        # Build chat messages
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_prompt(answers, rows, cols)},
        ]

        # Apply chat template
        prompt = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        sampler = make_sampler(temp=0.7)
        response = generate(
            model, tokenizer, prompt=prompt, max_tokens=1500, sampler=sampler
        )
        return parse_llm_response(response, rows, cols)
