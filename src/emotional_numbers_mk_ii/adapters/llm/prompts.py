"""Prompt templates for LLM rule generation."""

SYSTEM_PROMPT = """You are a Lumon Industries Macro Data Refinement supervisor designing a new data file.

Your job is to create classification rules that are:
1. INTERNALLY CONSISTENT - the rules must make sense, even if the sense is strange
2. DISCOVERABLE - a patient worker can figure out the pattern through observation
3. MYSTERIOUS - the connection to the worker's onboarding responses should be real but not obvious

The rules should feel meaningful, bureaucratically precise, yet slightly unsettling.
Think about what these numbers might "feel" like. What emotional quality connects them?

Example hidden rule ideas:
- "Numbers that would feel cold to touch"
- "Numbers in positions that spell something if you squint"
- "Numbers adjacent to exactly 2 other numbers of the same value"
- "Numbers in the corners of invisible rectangles"
- "Numbers that share a digit with the worker's compliance rating"
"""


def build_generation_prompt(answers: list[dict], rows: int, cols: int) -> str:
    """Build the rule generation prompt with answers context."""
    answers_formatted = "\n".join(
        f"- Question {a['questionId']}: {a['answer']}" for a in answers
    )

    return f"""{SYSTEM_PROMPT}

Worker onboarding responses:
{answers_formatted}

Design a data file for the {cols}x{rows} MDR terminal. Create classification regions.

Constraints:
- 5 target buckets (01-05), but you may create MORE regions that map to the same bucket
- Regions must not overlap
- Grid bounds: x in [0, {cols - 1}], y in [0, {rows - 1}]
- Each region: 4-16 cells
- Behaviors per bucket: jiggle_intensity (0.0-1.0), jiggle_frequency (0.5-2.0), sound_id (tone_01 through tone_05)

First decide your HIDDEN RULE for each bucket - what emotional quality connects those numbers?

Output ONLY this JSON structure (no other text):
{{
  "hidden_rules": {{
    "01": "description of what connects bucket 01 numbers",
    "02": "description",
    "03": "description",
    "04": "description",
    "05": "description"
  }},
  "regions": [
    {{"bucket": "01", "positions": [[5, 10], [6, 10], [5, 11], [6, 11]]}},
    {{"bucket": "02", "positions": [[20, 3], [21, 3], [22, 3], [20, 4], [21, 4]]}}
  ],
  "behaviors": [
    {{"bucket": "01", "jiggle_intensity": 0.3, "jiggle_frequency": 1.2, "sound_id": "tone_02"}},
    {{"bucket": "02", "jiggle_intensity": 0.7, "jiggle_frequency": 0.8, "sound_id": "tone_04"}}
  ]
}}"""
