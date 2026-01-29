"""Fixtures for web API tests."""

import pytest
from fastapi.testclient import TestClient

from emotional_numbers_mk_ii.adapters.web.api import HintResponse, StartResponse
from emotional_numbers_mk_ii.adapters.web.app import app


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
