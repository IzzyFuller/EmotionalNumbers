"""Fixtures for web API tests."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from emotional_numbers_mk_ii.adapters.web.api import (
    GameSession,
    HintResponse,
    StartResponse,
    router,
    set_session,
)
import sys
from pathlib import Path

# Add tests to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from adapters.mock_mlx_adapter import MLXQuestionGenerator, MLXRuleGenerator


@pytest.fixture
def test_app():
    """Create test app with mock generators injected."""
    from pathlib import Path
    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles

    app = FastAPI(title="LUMON MDR Terminal (Test)")
    app.include_router(router)

    # Inject mock generators
    session = GameSession(
        question_generator=MLXQuestionGenerator(),
        rule_generator=MLXRuleGenerator(),
    )
    set_session(session)

    base_dir = Path(__file__).parent.parent.parent / "src" / "emotional_numbers_mk_ii" / "adapters" / "web"
    app.mount("/static", StaticFiles(directory=base_dir / "static"), name="static")

    @app.get("/")
    async def index() -> FileResponse:
        return FileResponse(base_dir / "templates" / "index.html")

    return app


@pytest.fixture
def client(test_app):
    """Create test client with mock generators."""
    return TestClient(test_app)


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
