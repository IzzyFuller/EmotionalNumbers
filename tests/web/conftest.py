"""Fixtures for web API tests."""

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from emotional_numbers_mk_ii.adapters.web.api import HintResponse, StartResponse
from emotional_numbers_mk_ii.adapters.web.app import app
from emotional_numbers_mk_ii.adapters.llm.mlx_adapter import _reset_model


MOCK_QUESTIONS_RESPONSE = json.dumps({
    "questions": [
        {"id": "q1", "text": "What smell reminds you of safety?"},
        {"id": "q2", "text": "Describe the texture of comfort."},
        {"id": "q3", "text": "What color is your anxiety?"},
        {"id": "q4", "text": "Rate your compliance from 1-10."},
        {"id": "q5", "text": "What sound do you associate with work?"},
    ]
})

MOCK_RULES_RESPONSE = json.dumps({
    "hidden_rules": {
        "01": "Numbers that feel cold",
        "02": "Numbers that feel warm",
        "03": "Numbers that feel sharp",
        "04": "Numbers that feel soft",
        "05": "Numbers that feel heavy",
    },
    "regions": [
        {"bucket": "01", "positions": [[5, 10], [6, 10], [5, 11], [6, 11]]},
        {"bucket": "02", "positions": [[20, 3], [21, 3], [22, 3], [20, 4], [21, 4]]},
        {"bucket": "03", "positions": [[10, 15], [11, 15], [12, 15], [13, 15]]},
        {"bucket": "04", "positions": [[30, 20], [31, 20], [30, 21], [31, 21]]},
        {"bucket": "05", "positions": [[2, 2], [3, 2], [2, 3], [3, 3]]},
    ],
    "behaviors": [
        {"bucket": "01", "jiggle_intensity": 0.3, "jiggle_frequency": 1.2, "sound_id": "tone_01"},
        {"bucket": "02", "jiggle_intensity": 0.7, "jiggle_frequency": 1.1, "sound_id": "tone_02"},
        {"bucket": "03", "jiggle_intensity": 0.5, "jiggle_frequency": 1.5, "sound_id": "tone_03"},
        {"bucket": "04", "jiggle_intensity": 0.25, "jiggle_frequency": 1.0, "sound_id": "tone_04"},
        {"bucket": "05", "jiggle_intensity": 0.9, "jiggle_frequency": 0.6, "sound_id": "tone_05"},
    ],
})


@pytest.fixture(autouse=True)
def mock_mlx():
    """Mock MLX model loading and generation for all web tests."""
    _reset_model()

    mock_model = MagicMock()
    mock_tokenizer = MagicMock()
    # Pass through message content so mock_generate can distinguish
    mock_tokenizer.apply_chat_template.side_effect = lambda msgs, **kw: msgs[1]["content"]

    def mock_generate(model, tokenizer, prompt, max_tokens):
        # Return questions or rules based on prompt content
        if "onboarding questions" in prompt.lower():
            return MOCK_QUESTIONS_RESPONSE
        return MOCK_RULES_RESPONSE

    mock_mlx_lm = MagicMock()
    mock_mlx_lm.load.return_value = (mock_model, mock_tokenizer)
    mock_mlx_lm.generate.side_effect = mock_generate

    with patch.dict("sys.modules", {"mlx_lm": mock_mlx_lm}):
        yield

    _reset_model()


@pytest.fixture
def client():
    """Create test client for the FastAPI app."""
    return TestClient(app)


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
