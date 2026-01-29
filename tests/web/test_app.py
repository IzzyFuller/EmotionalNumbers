"""Tests for the FastAPI web application."""

import pytest
from fastapi.testclient import TestClient


class TestIndexRoute:
    """Tests for the index route serving the main HTML page."""

    def test_index_returns_200(self, client: TestClient):
        response = client.get("/")

        assert response.status_code == 200

    def test_index_returns_html_content_type(self, client: TestClient):
        response = client.get("/")

        assert "text/html" in response.headers["content-type"]

    def test_index_contains_terminal_structure(self, client: TestClient):
        response = client.get("/")

        assert b"LUMON MDR TERMINAL" in response.content
        assert b'id="grid"' in response.content
        assert b'class="bins-container"' in response.content


class TestStaticFiles:
    """Tests for static file serving."""

    def test_css_returns_200(self, client: TestClient):
        response = client.get("/static/terminal.css")

        assert response.status_code == 200

    def test_css_returns_css_content_type(self, client: TestClient):
        response = client.get("/static/terminal.css")

        assert "text/css" in response.headers["content-type"]

    def test_js_terminal_returns_200(self, client: TestClient):
        response = client.get("/static/js/terminal.js")

        assert response.status_code == 200

    def test_js_terminal_returns_javascript_content_type(self, client: TestClient):
        response = client.get("/static/js/terminal.js")

        content_type = response.headers["content-type"]
        assert "javascript" in content_type or "text/plain" in content_type

    def test_js_main_returns_200(self, client: TestClient):
        response = client.get("/static/js/main.js")

        assert response.status_code == 200

    def test_nonexistent_static_returns_404(self, client: TestClient):
        response = client.get("/static/nonexistent.file")

        assert response.status_code == 404


@pytest.fixture
def client():
    """Create test client for the FastAPI app."""
    from emotional_numbers_mk_ii.adapters.web.app import app

    return TestClient(app)
