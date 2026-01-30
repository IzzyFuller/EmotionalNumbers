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

Create 5 classification regions for a {cols}x{rows} grid. CRITICAL: Each region must have UNIQUE positions - NO overlapping cells between ANY regions.

Rules:
- Grid: x from 0 to {cols - 1}, y from 0 to {rows - 1}
- Each region: 4 to 8 cells forming a rectangle
- All 5 buckets (01-05) must have exactly one region each
- Spread regions across the grid - use different areas

Behavior constraints (IMPORTANT):
- sound_id MUST be "tone_01" through "tone_05" only. NEVER use "tone_00" (reserved).
- jiggle_intensity must be between 0.2 and 1.0. NEVER use 0.15 (reserved default).
- jiggle_frequency must be between 0.5 and 2.0. NEVER use exactly 0.8 (reserved default).

Based on the worker's answers, create hidden rules connecting each bucket to an emotional quality.

Output ONLY valid JSON:
{{
  "hidden_rules": {{
    "01": "numbers that feel [quality based on answers]",
    "02": "numbers that feel [different quality]",
    "03": "numbers that feel [different quality]",
    "04": "numbers that feel [different quality]",
    "05": "numbers that feel [different quality]"
  }},
  "regions": [
    {{"bucket": "01", "positions": [[2, 2], [3, 2], [2, 3], [3, 3]]}},
    {{"bucket": "02", "positions": [[10, 5], [11, 5], [12, 5], [10, 6], [11, 6], [12, 6]]}},
    {{"bucket": "03", "positions": [[25, 10], [26, 10], [25, 11], [26, 11]]}},
    {{"bucket": "04", "positions": [[15, 18], [16, 18], [17, 18], [15, 19], [16, 19], [17, 19]]}},
    {{"bucket": "05", "positions": [[32, 8], [33, 8], [34, 8], [32, 9], [33, 9], [34, 9]]}}
  ],
  "behaviors": [
    {{"bucket": "01", "jiggle_intensity": 0.25, "jiggle_frequency": 1.0, "sound_id": "tone_01"}},
    {{"bucket": "02", "jiggle_intensity": 0.5, "jiggle_frequency": 1.5, "sound_id": "tone_02"}},
    {{"bucket": "03", "jiggle_intensity": 0.35, "jiggle_frequency": 0.6, "sound_id": "tone_03"}},
    {{"bucket": "04", "jiggle_intensity": 0.7, "jiggle_frequency": 1.2, "sound_id": "tone_04"}},
    {{"bucket": "05", "jiggle_intensity": 0.4, "jiggle_frequency": 1.8, "sound_id": "tone_05"}}
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

        # Validate region size
        if not (4 <= len(region.positions) <= 16):
            raise RuleValidationError(
                f"Region size {len(region.positions)} out of range [4, 16]"
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

        response = generate(model, tokenizer, prompt=prompt, max_tokens=1500)
        return parse_llm_response(response, rows, cols)
