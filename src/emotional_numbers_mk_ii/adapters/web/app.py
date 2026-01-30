"""FastAPI app wiring - connects routes to the application."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from emotional_numbers_mk_ii.adapters.llm import LLMQuestionsAdapter, LLMRulesAdapter
from emotional_numbers_mk_ii.adapters.web.api import (
    GameSession,
    router,
    set_session,
)

BASE_DIR = Path(__file__).parent

# Create app
app = FastAPI(title="LUMON MDR Terminal")

# Wire up API routes
app.include_router(router)

# Initialize session with default (LLM) adapters
set_session(
    GameSession(
        questions_adapter=LLMQuestionsAdapter(),
        rules_adapter=LLMRulesAdapter(),
    )
)

# Static files
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


@app.get("/")
async def index() -> FileResponse:
    """Serve the main terminal interface."""
    return FileResponse(BASE_DIR / "templates" / "index.html")
