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

# Emotions response - LLM now only assigns emotions, regions are algorithmic
# Generate 20 mock assignments to match the 20 regions
MOCK_EMOTIONS_JSON = json.dumps(
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


def _mock_mlx_generate(model, tokenizer, prompt, max_tokens, sampler=None):  # noqa: ARG001
    """Mock for mlx_lm.generate - returns realistic JSON responses."""
    if "short questions" in prompt.lower() or "quirky corporate" in prompt.lower():
        return MOCK_QUESTIONS_JSON
    # Rules adapter now only calls LLM for emotional assignment
    return MOCK_EMOTIONS_JSON


def _mock_mlx_load(model_path):  # noqa: ARG001
    """Mock for mlx_lm.load - returns stub model/tokenizer tuple."""
    mock_model = MagicMock()
    mock_tokenizer = MagicMock()
    # Concatenate all message contents so mock detection works
    mock_tokenizer.apply_chat_template.side_effect = lambda msgs, **kwargs: " ".join(
        m["content"] for m in msgs
    )
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
    """Get hint, select tight boundary around region, return bucket.

    Select only cells immediately adjacent to the region (not a bounding box).
    This ensures the interior contains ONLY the region cells.
    """
    _ = playing_game  # Ensure game is started

    hint = HintResponse(**client.get("/api/hint").json())
    positions = hint.region.positions

    # Build tight boundary: only cells directly adjacent to region
    region_set = {(p[0], p[1]) for p in positions}
    boundary: set[tuple[int, int]] = set()

    for x, y in region_set:
        # Check all 4 neighbors
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if (nx, ny) not in region_set and nx >= 0 and ny >= 0:
                boundary.add((nx, ny))

    # Select all boundary cells
    for x, y in boundary:
        client.post("/api/select", json={"x": x, "y": y})

    return hint.region.bucket
