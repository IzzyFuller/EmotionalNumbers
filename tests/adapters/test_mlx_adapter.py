"""Tests for LLM adapters (rules and questions)."""

import json
from unittest.mock import MagicMock, patch

import pytest

from emotional_numbers_mk_ii.adapters.llm.model_loader import reset_model
from emotional_numbers_mk_ii.adapters.llm.rules_adapter import (
    LLMBehavior,
    LLMRegion,
    LLMRuleResponse,
    LLMRulesAdapter,
    RuleValidationError,
    convert_to_ruleset,
    parse_llm_response,
    validate_regions,
)
from emotional_numbers_mk_ii.domain.game import RuleSet


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_answers() -> list[dict]:
    """Sample onboarding answers."""
    return [
        {"questionId": "q1", "answer": "cinnamon"},
        {"questionId": "q2", "answer": "soft velvet"},
        {"questionId": "q3", "answer": "rain on windows"},
        {"questionId": "q4", "answer": "deep blue"},
        {"questionId": "q5", "answer": "7"},
    ]


@pytest.fixture
def valid_llm_response() -> str:
    """Valid JSON response from LLM."""
    return json.dumps(
        {
            "hidden_rules": {
                "01": "Numbers that feel cold",
                "02": "Numbers that feel warm",
                "03": "Numbers that feel sharp",
                "04": "Numbers that feel soft",
                "05": "Numbers that feel heavy",
            },
            "regions": [
                {"bucket": "01", "positions": [[5, 10], [6, 10], [5, 11], [6, 11]]},
                {
                    "bucket": "02",
                    "positions": [[20, 3], [21, 3], [22, 3], [20, 4], [21, 4]],
                },
                {"bucket": "03", "positions": [[10, 15], [11, 15], [12, 15], [13, 15]]},
                {"bucket": "04", "positions": [[30, 20], [31, 20], [30, 21], [31, 21]]},
                {"bucket": "05", "positions": [[2, 2], [3, 2], [2, 3], [3, 3]]},
            ],
            "behaviors": [
                {
                    "bucket": "01",
                    "jiggle_intensity": 0.3,
                    "jiggle_frequency": 1.2,
                    "sound_id": "tone_01",
                },
                {
                    "bucket": "02",
                    "jiggle_intensity": 0.7,
                    "jiggle_frequency": 0.8,
                    "sound_id": "tone_02",
                },
                {
                    "bucket": "03",
                    "jiggle_intensity": 0.5,
                    "jiggle_frequency": 1.5,
                    "sound_id": "tone_03",
                },
                {
                    "bucket": "04",
                    "jiggle_intensity": 0.2,
                    "jiggle_frequency": 1.0,
                    "sound_id": "tone_04",
                },
                {
                    "bucket": "05",
                    "jiggle_intensity": 0.9,
                    "jiggle_frequency": 0.6,
                    "sound_id": "tone_05",
                },
            ],
        }
    )


# ============================================================================
# Pydantic Model Tests
# ============================================================================


class TestLLMModels:
    """Test Pydantic models for LLM response."""

    def test_llm_region_converts_positions(self):
        """LLMRegion should convert list of lists to tuples."""
        region = LLMRegion(bucket="01", positions=[[1, 2], [3, 4]])
        assert region.positions == [(1, 2), (3, 4)]

    def test_llm_behavior_clamps_intensity(self):
        """LLMBehavior should clamp intensity to valid range."""
        behavior = LLMBehavior(
            bucket="01",
            jiggle_intensity=1.5,  # Out of range
            jiggle_frequency=1.0,
            sound_id="tone_01",
        )
        assert behavior.jiggle_intensity == 1.0

    def test_llm_behavior_clamps_frequency(self):
        """LLMBehavior should clamp frequency to valid range."""
        behavior = LLMBehavior(
            bucket="01",
            jiggle_intensity=0.5,
            jiggle_frequency=0.3,  # Below minimum
            sound_id="tone_01",
        )
        assert behavior.jiggle_frequency == 0.5


# ============================================================================
# Response Parsing Tests
# ============================================================================


class TestParseLLMResponse:
    """Test LLM response parsing."""

    def test_parses_valid_json(self, valid_llm_response):
        """Should parse valid JSON response."""
        rule_set = parse_llm_response(valid_llm_response, rows=25, cols=40)

        assert isinstance(rule_set, RuleSet)
        assert len(rule_set.regions) == 5
        assert len(rule_set.behaviors) == 5

    def test_extracts_json_from_preamble(self, valid_llm_response):
        """Should extract JSON even with preamble text."""
        response_with_preamble = f"Here is the data:\n{valid_llm_response}\nDone."
        rule_set = parse_llm_response(response_with_preamble, rows=25, cols=40)

        assert isinstance(rule_set, RuleSet)

    def test_raises_on_no_json(self):
        """Should raise error if no JSON found."""
        with pytest.raises(RuleValidationError, match="No JSON found"):
            parse_llm_response("No JSON here", rows=25, cols=40)


# ============================================================================
# Validation Tests
# ============================================================================


class TestValidateRegions:
    """Test region validation."""

    def test_accepts_valid_regions(self):
        """Should accept valid non-overlapping regions."""
        regions = [
            LLMRegion(bucket="01", positions=[(0, 0), (1, 0), (0, 1), (1, 1)]),
            LLMRegion(bucket="02", positions=[(5, 5), (6, 5), (5, 6), (6, 6)]),
        ]
        # Should not raise
        validate_regions(regions, rows=25, cols=40)

    def test_rejects_overlapping_regions(self):
        """Should reject overlapping regions."""
        regions = [
            LLMRegion(bucket="01", positions=[(0, 0), (1, 0), (0, 1), (1, 1)]),
            LLMRegion(
                bucket="02", positions=[(1, 1), (2, 1), (1, 2), (2, 2)]
            ),  # Overlaps at (1, 1)
        ]
        with pytest.raises(RuleValidationError, match="overlaps"):
            validate_regions(regions, rows=25, cols=40)

    def test_rejects_out_of_bounds(self):
        """Should reject positions outside grid."""
        regions = [
            LLMRegion(bucket="01", positions=[(50, 0), (51, 0), (50, 1), (51, 1)]),
        ]
        with pytest.raises(RuleValidationError, match="out of bounds"):
            validate_regions(regions, rows=25, cols=40)

    def test_rejects_invalid_bucket(self):
        """Should reject invalid bucket IDs."""
        regions = [
            LLMRegion(bucket="99", positions=[(0, 0), (1, 0), (0, 1), (1, 1)]),
        ]
        with pytest.raises(RuleValidationError, match="Invalid bucket"):
            validate_regions(regions, rows=25, cols=40)

    def test_rejects_too_small_region(self):
        """Should reject regions with fewer than 2 cells."""
        regions = [
            LLMRegion(bucket="01", positions=[(0, 0)]),  # Only 1 cell
        ]
        with pytest.raises(RuleValidationError, match="out of range"):
            validate_regions(regions, rows=25, cols=40)

    def test_rejects_too_large_region(self):
        """Should reject regions with more than 20 cells."""
        positions = [(x, y) for x in range(5) for y in range(5)]  # 25 cells
        regions = [LLMRegion(bucket="01", positions=positions)]
        with pytest.raises(RuleValidationError, match="out of range"):
            validate_regions(regions, rows=25, cols=40)


# ============================================================================
# Convert to RuleSet Tests
# ============================================================================


class TestConvertToRuleset:
    """Test conversion to domain RuleSet."""

    def test_converts_regions(self):
        """Should convert LLM regions to domain regions."""
        response = LLMRuleResponse(
            hidden_rules={"01": "test"},
            regions=[
                LLMRegion(bucket="01", positions=[(0, 0), (1, 0), (0, 1), (1, 1)])
            ],
            behaviors=[
                LLMBehavior(
                    bucket="01",
                    jiggle_intensity=0.5,
                    jiggle_frequency=1.0,
                    sound_id="tone_01",
                )
            ],
        )
        rule_set = convert_to_ruleset(response)

        assert len(rule_set.regions) == 1
        assert rule_set.regions[0].bucket == "01"
        assert rule_set.regions[0].positions == [(0, 0), (1, 0), (0, 1), (1, 1)]

    def test_converts_behaviors(self):
        """Should convert LLM behaviors to domain behaviors."""
        response = LLMRuleResponse(
            hidden_rules={"01": "test"},
            regions=[
                LLMRegion(bucket="01", positions=[(0, 0), (1, 0), (0, 1), (1, 1)])
            ],
            behaviors=[
                LLMBehavior(
                    bucket="01",
                    jiggle_intensity=0.5,
                    jiggle_frequency=1.0,
                    sound_id="tone_01",
                )
            ],
        )
        rule_set = convert_to_ruleset(response)

        assert len(rule_set.behaviors) == 1
        assert rule_set.behaviors[0].bucket == "01"
        assert rule_set.behaviors[0].jiggle_intensity == 0.5
        assert rule_set.behaviors[0].sound_id == "tone_01"


# ============================================================================
# LLMRulesAdapter Tests
# ============================================================================


class TestLLMRulesAdapter:
    """Test LLM-based rules adapter."""

    def test_generates_with_mocked_mlx(self, sample_answers, valid_llm_response):
        """Should generate rules with mocked MLX."""
        reset_model()  # Clear singleton

        mock_model = MagicMock()
        mock_tokenizer = MagicMock()
        mock_tokenizer.apply_chat_template.return_value = "formatted prompt"

        # Create mock mlx_lm module and submodules
        mock_mlx_lm = MagicMock()
        mock_mlx_lm.load.return_value = (mock_model, mock_tokenizer)
        mock_mlx_lm.generate.return_value = valid_llm_response

        mock_sample_utils = MagicMock()
        mock_sample_utils.make_sampler.return_value = MagicMock()

        with patch.dict(
            "sys.modules",
            {"mlx_lm": mock_mlx_lm, "mlx_lm.sample_utils": mock_sample_utils},
        ):
            adapter = LLMRulesAdapter()
            rule_set = adapter.generate_rules(sample_answers, rows=25, cols=40)

        assert isinstance(rule_set, RuleSet)
        assert len(rule_set.regions) == 5

        reset_model()  # Clean up
