"""Tests for the game API endpoints.

Tests the API the way the UI would call it - no knowledge of internals.
"""

from fastapi.testclient import TestClient

from emotional_numbers_mk_ii.adapters.web.api import (
    AnswersResponse,
    ClassifyResponse,
    ClearResponse,
    HintResponse,
    SelectResponse,
    StartResponse,
    StateResponse,
)


class TestGameSession:
    """Tests for starting and managing game sessions."""

    def test_start_returns_questions(self, client: TestClient):
        """Starting a game returns onboarding questions."""
        response = client.post("/api/start")

        assert response.status_code == 200
        data = StartResponse(**response.json())
        assert len(data.questions) > 0

    def test_submit_answers_starts_game(self, client: TestClient):
        """Submitting answers transitions to playing phase with a grid."""
        client.post("/api/start")
        response = client.post(
            "/api/answers", json={"answers": [{"questionId": "q1", "answer": "test"}]}
        )

        assert response.status_code == 200
        data = AnswersResponse(**response.json())
        assert data.phase == "playing"
        assert len(data.grid) == 25
        assert len(data.grid[0]) == 40

    def test_same_answers_produce_same_grid(self, client: TestClient):
        """Deterministic: same answers always produce the same puzzle."""
        answers = [{"questionId": "q1", "answer": "cake"}]

        client.post("/api/start")
        grid1 = AnswersResponse(
            **client.post("/api/answers", json={"answers": answers}).json()
        ).grid

        client.post("/api/start")
        grid2 = AnswersResponse(
            **client.post("/api/answers", json={"answers": answers}).json()
        ).grid

        assert grid1 == grid2

    def test_different_answers_produce_different_grid(self, client: TestClient):
        """Different answers produce different puzzles."""
        client.post("/api/start")
        grid1 = AnswersResponse(
            **client.post(
                "/api/answers",
                json={"answers": [{"questionId": "q1", "answer": "cake"}]},
            ).json()
        ).grid

        client.post("/api/start")
        grid2 = AnswersResponse(
            **client.post(
                "/api/answers",
                json={"answers": [{"questionId": "q1", "answer": "pie"}]},
            ).json()
        ).grid

        assert grid1 != grid2


class TestGameState:
    """Tests for getting game state."""

    def test_get_state_returns_grid_bins_progress(
        self, client: TestClient, playing_game
    ):
        """Game state includes grid, bins, and progress."""
        data = StateResponse(**client.get("/api/state").json())

        assert len(data.grid) == 25
        assert len(data.grid[0]) == 40
        assert data.progress == 0
        assert set(data.bins.keys()) == {"01", "02", "03", "04", "05"}


class TestSelection:
    """Tests for selecting cells."""

    def test_select_and_deselect(self, client: TestClient, playing_game):
        """Toggling selects then deselects a cell."""
        # Select
        data = SelectResponse(
            **client.post("/api/select", json={"x": 5, "y": 5}).json()
        )
        assert [5, 5] in data.selected

        # Deselect
        data = SelectResponse(
            **client.post("/api/select", json={"x": 5, "y": 5}).json()
        )
        assert [5, 5] not in data.selected

    def test_clear_selection(self, client: TestClient, playing_game):
        """Clear removes all selections."""
        client.post("/api/select", json={"x": 5, "y": 5})
        client.post("/api/select", json={"x": 6, "y": 6})

        data = ClearResponse(**client.post("/api/clear").json())
        assert data.selected == []


class TestClassification:
    """Tests for classifying selections into buckets."""

    def test_correct_classification_succeeds(
        self, client: TestClient, playing_game, select_hinted_region
    ):
        """Classifying cells to the correct bucket succeeds."""
        bucket = select_hinted_region

        data = ClassifyResponse(
            **client.post("/api/classify", json={"bucket": bucket}).json()
        )

        assert data.success is True
        assert data.classified_count > 0
        assert data.bins[bucket] > 0

    def test_wrong_bucket_fails(
        self, client: TestClient, playing_game, select_hinted_region
    ):
        """Classifying cells to the wrong bucket fails."""
        correct_bucket = select_hinted_region
        wrong_bucket = "02" if correct_bucket != "02" else "01"

        data = ClassifyResponse(
            **client.post("/api/classify", json={"bucket": wrong_bucket}).json()
        )

        assert data.success is False
        assert data.classified_count == 0

    def test_failed_classification_clears_selection(
        self, client: TestClient, playing_game, select_hinted_region
    ):
        """Failed classification clears the selection."""
        correct_bucket = select_hinted_region
        wrong_bucket = "02" if correct_bucket != "02" else "01"

        client.post("/api/classify", json={"bucket": wrong_bucket})

        data = SelectResponse(
            **client.post("/api/select", json={"x": 0, "y": 0}).json()
        )
        # Only the new selection should be present (old ones cleared)
        assert len(data.selected) == 1


class TestHints:
    """Tests for the hint system."""

    def test_hint_returns_region_with_positions(self, client: TestClient, playing_game):
        """Hint returns a bucket and positions to select."""
        data = HintResponse(**client.get("/api/hint").json())

        assert data.region is not None
        assert data.region.bucket in {"01", "02", "03", "04", "05"}
        assert len(data.region.positions) > 0
