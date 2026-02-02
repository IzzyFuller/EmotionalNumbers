"""Tests for LLM rules adapter."""

import json
from unittest.mock import MagicMock, patch

import pytest

from emotional_numbers_mk_ii.adapters.llm.model_loader import reset_model
from emotional_numbers_mk_ii.adapters.llm.rules_adapter import (
    EmotionAssignment,
    LLMRulesAdapter,
)
from emotional_numbers_mk_ii.adapters.llm.region_generator import generate_regions
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
    ]


@pytest.fixture
def valid_emotions_response() -> str:
    """Valid emotions JSON response from LLM - 20 regions mapped to 5 buckets."""
    return json.dumps(
        {
            "assignments": [
                {
                    "region_id": i,
                    "bucket": f"{(i % 5) + 1:02d}",
                    "rule": ["cold", "warm", "sharp", "soft", "heavy"][i % 5],
                    "intensity": 0.3 + (i % 5) * 0.15,
                    "frequency": 0.6 + (i % 5) * 0.2,
                }
                for i in range(1, 21)
            ]
        }
    )


# ============================================================================
# Region Generator Tests
# ============================================================================


class TestRegionGenerator:
    """Test algorithmic region generation."""

    def test_generates_non_overlapping_regions(self):
        """Should generate regions with no overlapping cells."""
        regions = generate_regions(rows=25, cols=40, num_regions=5, seed=42)

        all_positions = []
        for region in regions:
            all_positions.extend(region.positions)

        # No duplicates
        assert len(all_positions) == len(set(all_positions))

    def test_generates_requested_number_of_regions(self):
        """Should generate the requested number of regions."""
        regions = generate_regions(rows=25, cols=40, num_regions=5, seed=42)
        assert len(regions) == 5

    def test_deterministic_with_same_seed(self):
        """Same seed should produce same regions."""
        regions1 = generate_regions(rows=25, cols=40, num_regions=5, seed=123)
        regions2 = generate_regions(rows=25, cols=40, num_regions=5, seed=123)

        for r1, r2 in zip(regions1, regions2):
            assert r1.positions == r2.positions

    def test_different_seeds_produce_different_regions(self):
        """Different seeds should produce different regions."""
        regions1 = generate_regions(rows=25, cols=40, num_regions=5, seed=123)
        regions2 = generate_regions(rows=25, cols=40, num_regions=5, seed=456)

        positions1 = [r.positions for r in regions1]
        positions2 = [r.positions for r in regions2]
        assert positions1 != positions2


# ============================================================================
# Emotion Models Tests
# ============================================================================


class TestEmotionModels:
    """Test Pydantic models for emotions."""

    def test_clamps_intensity(self):
        """Should clamp intensity to valid range."""
        assignment = EmotionAssignment(
            region_id=1, bucket="01", rule="test", intensity=1.5, frequency=1.0
        )
        assert assignment.intensity == 1.0

    def test_clamps_frequency(self):
        """Should clamp frequency to valid range."""
        assignment = EmotionAssignment(
            region_id=1, bucket="01", rule="test", intensity=0.5, frequency=0.3
        )
        assert assignment.frequency == 0.5


# ============================================================================
# LLMRulesAdapter Tests
# ============================================================================


class TestLLMRulesAdapter:
    """Test hybrid rules adapter."""

    def test_generates_rules_with_mocked_llm(
        self, sample_answers, valid_emotions_response
    ):
        """Should generate rules: algorithmic regions + mocked LLM emotions."""
        reset_model()

        with (
            patch("mlx_lm.load") as mock_load,
            patch("mlx_lm.generate", return_value=valid_emotions_response),
            patch("mlx_lm.sample_utils.make_sampler", return_value=MagicMock()),
        ):
            mock_tokenizer = MagicMock()
            mock_tokenizer.apply_chat_template.return_value = "prompt"
            mock_load.return_value = (MagicMock(), mock_tokenizer)

            adapter = LLMRulesAdapter()
            rule_set = adapter.generate_rules(sample_answers, rows=25, cols=40)

        assert isinstance(rule_set, RuleSet)
        assert len(rule_set.regions) == 20
        assert len(rule_set.behaviors) == 5  # One behavior per bucket, not per region

        reset_model()

    def test_same_answers_produce_same_regions(self, valid_emotions_response):
        """Same answers should produce same region positions (deterministic seed)."""
        reset_model()

        answers = [{"questionId": "q1", "answer": "test"}]

        with (
            patch("mlx_lm.load") as mock_load,
            patch("mlx_lm.generate", return_value=valid_emotions_response),
            patch("mlx_lm.sample_utils.make_sampler", return_value=MagicMock()),
        ):
            mock_tokenizer = MagicMock()
            mock_tokenizer.apply_chat_template.return_value = "prompt"
            mock_load.return_value = (MagicMock(), mock_tokenizer)

            adapter = LLMRulesAdapter()
            rules1 = adapter.generate_rules(answers, rows=25, cols=40)
            rules2 = adapter.generate_rules(answers, rows=25, cols=40)

        positions1 = [r.positions for r in rules1.regions]
        positions2 = [r.positions for r in rules2.regions]
        assert positions1 == positions2

        reset_model()
