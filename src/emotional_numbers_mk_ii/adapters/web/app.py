"""FastAPI app to serve the MDR Terminal UI."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).parent

app = FastAPI(title="LUMON MDR Terminal")

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


@app.get("/")
async def index() -> FileResponse:
    """Serve the main terminal interface."""
    return FileResponse(BASE_DIR / "templates" / "index.html")
