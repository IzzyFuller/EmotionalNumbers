"""Fixtures for web API tests."""

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from emotional_numbers_mk_ii.adapters.deterministic import (
    DeterministicQuestionsAdapter,
    DeterministicRulesAdapter,
)
from emotional_numbers_mk_ii.adapters.llm import (
    LLMQuestionsAdapter,
    LLMRulesAdapter,
    reset_model,
)
from emotional_numbers_mk_ii.adapters.web.api import (
    GameSession,
    HintResponse,
    StartResponse,
    set_session,
)
from emotional_numbers_mk_ii.adapters.web.app import app


# ============================================================================
# Mock Data for LLM Boundary
# ============================================================================

MOCK_QUESTIONS_JSON = json.dumps(
    {
        "questions": [
            {"id": "q1", "text": "What smell reminds you of safety?"},
            {"id": "q2", "text": "Describe the texture of comfort."},
            {"id": "q3", "text": "What color is your anxiety?"},
            {"id": "q4", "text": "Rate your compliance from 1-10."},
            {"id": "q5", "text": "What sound do you associate with work?"},
        ]
    }
)

MOCK_RULES_JSON = json.dumps(
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
                "jiggle_frequency": 1.1,
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
                "jiggle_intensity": 0.25,
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


def _mock_mlx_generate(model, tokenizer, prompt, max_tokens, sampler=None):  # noqa: ARG001
    """Mock for mlx_lm.generate - returns realistic JSON responses."""
    if "short questions" in prompt.lower():
        return MOCK_QUESTIONS_JSON
    return MOCK_RULES_JSON


def _mock_mlx_load(model_path):  # noqa: ARG001
    """Mock for mlx_lm.load - returns stub model/tokenizer tuple."""
    mock_model = MagicMock()
    mock_tokenizer = MagicMock()
    mock_tokenizer.apply_chat_template.side_effect = lambda msgs, **kwargs: msgs[1][
        "content"
    ]  # noqa: ARG005
    return mock_model, mock_tokenizer


def _mock_make_sampler(temp=0.0):  # noqa: ARG001
    """Mock for mlx_lm.sample_utils.make_sampler."""
    return MagicMock()


# ============================================================================
# Adapter Fixtures - Direct instances, no conditionals
# ============================================================================


@pytest.fixture(
    params=[
        pytest.param(DeterministicQuestionsAdapter(seed=42), id="deterministic"),
        pytest.param(LLMQuestionsAdapter(), id="llm"),
    ]
)
def questions_adapter(request):
    """Parameterized questions adapter."""
    return request.param


@pytest.fixture(
    params=[
        pytest.param(DeterministicRulesAdapter(), id="deterministic"),
        pytest.param(LLMRulesAdapter(), id="llm"),
    ]
)
def rules_adapter(request):
    """Parameterized rules adapter."""
    return request.param


# ============================================================================
# Test Client
# ============================================================================


@pytest.fixture
def client(questions_adapter, rules_adapter):
    """Test client with injected adapters. mlx_lm mocked at boundary."""
    reset_model()

    session = GameSession(
        questions_adapter=questions_adapter,
        rules_adapter=rules_adapter,
    )
    set_session(session)

    with (
        patch("mlx_lm.load", side_effect=_mock_mlx_load),
        patch("mlx_lm.generate", side_effect=_mock_mlx_generate),
        patch("mlx_lm.sample_utils.make_sampler", side_effect=_mock_make_sampler),
    ):
        yield TestClient(app)

    reset_model()


# ============================================================================
# Game State Fixtures
# ============================================================================


@pytest.fixture
def playing_game(client: TestClient):
    """Start a game and complete onboarding."""
    start_response = client.post("/api/start")
    start_data = StartResponse(**start_response.json())

    answers = [{"questionId": q.id, "answer": "test"} for q in start_data.questions]
    client.post("/api/answers", json={"answers": answers})


@pytest.fixture
def select_hinted_region(client: TestClient, playing_game) -> str:
    """Get hint, select boundary around region, return bucket.

    Boundary-based classification: select cells surrounding the region.
    """
    _ = playing_game  # Ensure game is started

    hint = HintResponse(**client.get("/api/hint").json())
    positions = hint.region.positions

    # Calculate boundary: cells surrounding the region
    region_set = {(p[0], p[1]) for p in positions}
    min_x, max_x = min(p[0] for p in positions), max(p[0] for p in positions)
    min_y, max_y = min(p[1] for p in positions), max(p[1] for p in positions)

    for x in range(min_x - 1, max_x + 2):
        for y in range(min_y - 1, max_y + 2):
            if (x, y) not in region_set and x >= 0 and y >= 0:
                if x in (min_x - 1, max_x + 1) or y in (min_y - 1, max_y + 1):
                    client.post("/api/select", json={"x": x, "y": y})

    return hint.region.bucket
