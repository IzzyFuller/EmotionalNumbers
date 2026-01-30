"""Fixtures for web API tests with parameterized adapter combinations."""

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


# ============================================================================
# Mock LLM Responses (for boundary mocking)
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


def _create_mock_mlx_lm():
    """Create mock mlx_lm module - only mocks load() and generate()."""
    mock_model = MagicMock()
    mock_tokenizer = MagicMock()
    mock_tokenizer.apply_chat_template.side_effect = lambda msgs, **kw: msgs[1][
        "content"
    ]

    def mock_generate(model, tokenizer, prompt, max_tokens):
        if "onboarding questions" in prompt.lower():
            return MOCK_QUESTIONS_JSON
        return MOCK_RULES_JSON

    mock_mlx_lm = MagicMock()
    mock_mlx_lm.load.return_value = (mock_model, mock_tokenizer)
    mock_mlx_lm.generate.side_effect = mock_generate
    return mock_mlx_lm


# ============================================================================
# Parameterized Adapter Fixtures
# ============================================================================


@pytest.fixture(
    params=[
        pytest.param("llm", id="llm-questions"),
        pytest.param("deterministic", id="deterministic-questions"),
    ],
)
def questions_adapter_type(request):
    """Parameterized questions adapter type."""
    return request.param


@pytest.fixture(
    params=[
        pytest.param("llm", id="llm-rules"),
        pytest.param("deterministic", id="deterministic-rules"),
    ],
)
def rules_adapter_type(request):
    """Parameterized rules adapter type."""
    return request.param


@pytest.fixture
def questions_adapter(questions_adapter_type):
    """Create questions adapter based on type."""
    if questions_adapter_type == "llm":
        return LLMQuestionsAdapter()
    return DeterministicQuestionsAdapter(seed=42)


@pytest.fixture
def rules_adapter(rules_adapter_type):
    """Create rules adapter based on type."""
    if rules_adapter_type == "llm":
        return LLMRulesAdapter()
    return DeterministicRulesAdapter()


# ============================================================================
# Test Client Fixtures
# ============================================================================


@pytest.fixture
def client(questions_adapter_type, rules_adapter_type):
    """Create test client with parameterized adapters.

    LLM adapters have mlx_lm mocked at the boundary.
    Deterministic adapters run pure logic with no mocking.
    """
    reset_model()

    # Determine if we need mocking (any LLM adapter)
    needs_mock = questions_adapter_type == "llm" or rules_adapter_type == "llm"

    # Create adapters
    if questions_adapter_type == "llm":
        questions_adapter = LLMQuestionsAdapter()
    else:
        questions_adapter = DeterministicQuestionsAdapter(seed=42)

    if rules_adapter_type == "llm":
        rules_adapter = LLMRulesAdapter()
    else:
        rules_adapter = DeterministicRulesAdapter()

    # Create session with adapters
    session = GameSession(
        questions_adapter=questions_adapter,
        rules_adapter=rules_adapter,
    )

    if needs_mock:
        with patch.dict("sys.modules", {"mlx_lm": _create_mock_mlx_lm()}):
            # Import app fresh within mock context
            set_session(session)
            from emotional_numbers_mk_ii.adapters.web.app import app

            yield TestClient(app)
    else:
        # Pure deterministic - no mocking needed
        set_session(session)
        from emotional_numbers_mk_ii.adapters.web.app import app

        yield TestClient(app)

    reset_model()


@pytest.fixture
def playing_game(client: TestClient):
    """Start a game and complete onboarding."""
    start_response = client.post("/api/start")
    start_data = StartResponse(**start_response.json())

    answers = [{"questionId": q.id, "answer": "test"} for q in start_data.questions]
    client.post("/api/answers", json={"answers": answers})


@pytest.fixture
def select_hinted_region(client: TestClient, playing_game) -> str:
    """Get hint, select all positions in the region, return the bucket."""
    hint = HintResponse(**client.get("/api/hint").json())
    for pos in hint.region.positions:
        client.post("/api/select", json={"x": pos[0], "y": pos[1]})
    return hint.region.bucket
